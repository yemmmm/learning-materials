#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-09
# Context: 用户拒绝源码修改；对照正常/异常环境的Agent实际授权配置。只读，不补白名单、不改配置、不重启。
# Cmds: 3条；两套环境各执行一次，回传时注明正常/异常。沿用原部署目录和当前shell中的docker-compose函数。
# 正常环境选择“非维护者也能访问”的账号+Agent；异常环境选择仍打不开、未被单点补权的Agent。
# 鉴权探针可能产生检查日志，不把它当作浏览器原始请求日志。不回传邮箱、Token、Cookie或内部地址。

# 1. 在当前环境输入目标Agent UUID和该访问者邮箱/账号UUID。
read -r -p 'Agent UUID: ' DTR_AGENT_ID
read -r -p 'Visitor email (or account UUID): ' DTR_ACCOUNT_ID

# 2. 只输出当前Compose相关服务的版本与两个RBAC开关，最多12行；不输出完整环境变量或镜像仓库地址。
docker inspect $(docker-compose ps -q) | docker-compose exec -T api python -c '
import json,sys
rows=json.load(sys.stdin)
shown=0
for row in rows:
 c=row.get("Config") or {}; service=(c.get("Labels") or {}).get("com.docker.compose.service","")
 if service in ("worker","worker_beat"): continue
 image=c.get("Image",""); base=image.rsplit("/",1)[-1]
 if not any(x in service.lower() for x in ("api","websocket","enterprise","rbac","web")) and base.split(":")[0]!="dify-ee": continue
 env=dict(x.split("=",1) for x in c.get("Env") or [] if "=" in x)
 def flag(k):
  v=env.get(k)
  return "UNSET" if v is None else v if v.lower() in ("true","false","1","0") else "OTHER_VALUE"
 version=base.rsplit(":",1)[-1] if ":" in base and "@" not in base else "UNSPECIFIED_OR_DIGEST"
 print(json.dumps({"service":service,"version":version,"RBAC_ENABLED":flag("RBAC_ENABLED"),"ENTERPRISE_ENABLED":flag("ENTERPRISE_ENABLED")}))
 shown+=1
 if shown>=12: break
'

# 3. 只读查询账号/Agent映射、角色、白名单、策略和实际鉴权结果；最多30行。若API的RBAC关闭则跳过RBAC服务查询。
docker-compose exec -T -e DTR_AGENT_ID="$DTR_AGENT_ID" -e DTR_ACCOUNT_ID="$DTR_ACCOUNT_ID" api python - <<'PYCODE' | tail -30
import os,json,logging
from uuid import UUID
logging.disable(logging.CRITICAL)
def emit(kind, **data): print(json.dumps({"check":kind,**data},ensure_ascii=True,default=str))
def main():
 from configs import dify_config
 from sqlalchemy import create_engine,text
 from services.enterprise.base import EnterpriseRequest
 emit("effective_api_flags",RBAC_ENABLED=dify_config.RBAC_ENABLED,ENTERPRISE_ENABLED=dify_config.ENTERPRISE_ENABLED)
 agent_id=str(UUID(os.environ["DTR_AGENT_ID"]))
 account_input=os.environ["DTR_ACCOUNT_ID"].strip()
 try: account_id=str(UUID(account_input))
 except ValueError: account_id=None
 # 只执行SELECT；显式只读事务，不调用App工厂或创建/修复Agent会话。
 engine=create_engine(dify_config.SQLALCHEMY_DATABASE_URI)
 with engine.connect() as conn:
  conn.execute(text("SET TRANSACTION READ ONLY"))
  if account_id is None:
   accounts=conn.execute(text("SELECT id FROM accounts WHERE lower(email)=lower(:email) LIMIT 2"),{"email":account_input}).all()
   if len(accounts)!=1:
    emit("STOP",reason="EMAIL_NOT_FOUND" if not accounts else "EMAIL_MATCHES_MULTIPLE_ACCOUNTS"); return
   account_id=str(accounts[0][0])
  agent=conn.execute(text("SELECT a.tenant_id,a.app_id,a.scope,a.source,a.status AS agent_status,a.created_by,a.backing_app_id,p.maintainer,p.status AS app_status FROM agents a LEFT JOIN apps p ON p.id=a.app_id AND p.tenant_id=a.tenant_id WHERE a.id=:id"),{"id":agent_id}).mappings().first()
  if not agent:
   emit("STOP",reason="AGENT_NOT_FOUND"); return
  tenant_id=str(agent["tenant_id"])
  member=conn.execute(text("SELECT role FROM tenant_account_joins WHERE tenant_id=:t AND account_id=:a"),{"t":tenant_id,"a":account_id}).first()
  app_id=str(agent["app_id"]) if agent["app_id"] else None
  emit("target",agent_id=agent_id,account_id=account_id)
  emit("resource",authz_app_id=app_id,scope=agent["scope"],source=agent["source"],agent_status=agent["agent_status"])
  emit("membership",in_workspace=member is not None,legacy_role=member[0] if member else None,is_maintainer=str(agent["maintainer"])==account_id,is_creator=str(agent["created_by"])==account_id,app_status=agent["app_status"])
  if not member or not app_id:
   emit("STOP",reason="MEMBER_OR_AUTHZ_APP_MISSING"); return
 if not dify_config.RBAC_ENABLED:
  emit("rbac_checks",skipped="API_RBAC_DISABLED"); return
 def call(label,method,endpoint,**kwargs):
  try:
   data=EnterpriseRequest.send_inner_rbac_request(method,"/rbac/"+endpoint,tenant_id=tenant_id,account_id=account_id,timeout=10,**kwargs)
   if not isinstance(data,dict):
    emit(label,error="UNEXPECTED_RESPONSE_TYPE",response_type=type(data).__name__); return None
   return data
  except Exception as exc:
   # 不打印异常正文，避免连接串、请求头或业务内容进入回传。
   emit(label,error=type(exc).__name__,status=getattr(exc,"status_code",None)); return None
 role_data=call("roles","GET","members/rbac-roles",params={"account_id":account_id})
 keys={"agent.manage","app.acl.view_layout","app.acl.edit","app.acl.test_and_run"}
 if role_data is not None:
  roles=role_data.get("roles") or []
  emit("roles",count=len(roles),shown=min(len(roles),6))
  for r in roles[:6]: emit("role",id=r.get("id"),role_tag=r.get("role_tag"),category=r.get("category"),permission_keys=sorted(keys.intersection(r.get("permission_keys") or [])))
 whitelist=call("whitelist","GET","apps/whitelist",params={"app_id":app_id})
 if whitelist is not None:
  ids=whitelist.get("account_ids")
  emit("whitelist",account_ids_present=isinstance(ids,list),count=len(ids) if isinstance(ids,list) else None,contains_account=account_id in ids if isinstance(ids,list) else None)
 policies=call("policies","GET","apps/user-access-policies",params={"app_id":app_id})
 if policies is not None:
  rows=[r for r in (policies.get("data") or []) if (r.get("account") or {}).get("account_id")==account_id]
  emit("policies",scope=policies.get("scope"),target_rows=len(rows),policy_keys=[p.get("policy_key") for r in rows for p in (r.get("access_policies") or [])][:8])
 for scene in ("agent_manage","app_view_layout","app_edit","app_test_and_run"):
  payload={"tenant_id":tenant_id,"account_id":account_id,"scene":scene}
  if scene!="agent_manage": payload.update(resource_type="app",resource_id=app_id)
  data=call(scene,"POST","check-access",json=payload)
  if data is not None:
   emit(scene,allowed=data.get("allowed","MISSING"),reason=data.get("reason","MISSING"))
   emit(scene,matched_roles=len(data["matched_role_ids"]) if isinstance(data.get("matched_role_ids"),list) else "MISSING",account_roles=len(data["account_role_ids"]) if isinstance(data.get("account_role_ids"),list) else "MISSING")
try:
 main()
except Exception as exc:
 emit("STOP",error=type(exc).__name__)
PYCODE
