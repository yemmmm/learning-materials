#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-09
# Context: 3.12.0同环境账号访问不对称；原探针ValueError未定位。只读核对实际可访问账号与反向拒绝，禁止源码修改。
# Cmds: 2条；本轮只需3.12.0，不重查已确认的服务开关。保持原部署目录、同一shell中的docker-compose函数。
# 第一次：A（能看别人Agent的账号）+B创建且A能打开的Agent。
# 第二次：B（不能看A的Agent的账号）+A创建且B打不开的Agent。回传注明A看B/B看A。
# 不写配置、角色、白名单或数据库；鉴权探针可能产生检查日志。不要回传Token/Cookie/邮箱。

# 1. 输入目标Agent UUID或完整/agents/...地址，以及当前访问者邮箱/账号UUID。等待每次提示后输入，再执行命令2。
read -r -p 'Target Agent UUID or /agents/... URL: ' DTR_AGENT_ID
read -r -p 'Visitor email (or account UUID): ' DTR_ACCOUNT_ID

# 2. 只读比较维护者关系、角色、白名单、个人策略和实际鉴权；最多30行。输入错误会明确标记字段，其他错误标记阶段和代码行，不打印敏感异常正文。
docker-compose exec -T -e DTR_AGENT_ID="$DTR_AGENT_ID" -e DTR_ACCOUNT_ID="$DTR_ACCOUNT_ID" api python - <<'PYCODE' | tail -30
import os,json,logging,traceback
from urllib.parse import urlsplit
stage="start"
from uuid import UUID
logging.disable(logging.CRITICAL)
def emit(kind, **data): print(json.dumps({"check":kind,**data},ensure_ascii=True,default=str))
def parse_agent_ref(raw):
 value=raw.strip()
 if "/" in value:
  parts=[p for p in urlsplit(value).path.split("/") if p]
  try: value=parts[parts.index("agents")+1]
  except (ValueError,IndexError): raise ValueError("INVALID_AGENT_REFERENCE") from None
 return str(UUID(value))
def main():
 global stage
 stage="load_config"
 from configs import dify_config
 from sqlalchemy import create_engine,text
 from services.enterprise.base import EnterpriseRequest
 emit("probe",version="AGENT_ASYMMETRY_V2")
 emit("effective_api_flags",RBAC_ENABLED=dify_config.RBAC_ENABLED,ENTERPRISE_ENABLED=dify_config.ENTERPRISE_ENABLED)
 stage="parse_agent_reference"
 raw_agent=os.environ.get("DTR_AGENT_ID","")
 try: agent_id=parse_agent_ref(raw_agent)
 except ValueError:
  emit("STOP",stage=stage,reason="INVALID_AGENT_REFERENCE",input_length=len(raw_agent.strip()),hint="Use Agent UUID or /agents/UUID URL"); return
 stage="parse_account_input"
 account_input=os.environ.get("DTR_ACCOUNT_ID","").strip()
 if not account_input:
  emit("STOP",stage=stage,reason="EMPTY_ACCOUNT_INPUT"); return
 try: account_id=str(UUID(account_input))
 except ValueError:
  if "@" not in account_input:
   emit("STOP",stage=stage,reason="EXPECTED_EMAIL_OR_ACCOUNT_UUID"); return
  account_id=None
 # 只执行SELECT；显式只读事务，不调用App工厂或创建/修复Agent会话。
 stage="database_connect"
 engine=create_engine(dify_config.SQLALCHEMY_DATABASE_URI)
 with engine.connect() as conn:
  conn.execute(text("SET TRANSACTION READ ONLY"))
  if account_id is None:
   stage="resolve_account_email"
   accounts=conn.execute(text("SELECT id FROM accounts WHERE lower(email)=lower(:email) LIMIT 2"),{"email":account_input}).all()
   if len(accounts)!=1:
    emit("STOP",reason="EMAIL_NOT_FOUND" if not accounts else "EMAIL_MATCHES_MULTIPLE_ACCOUNTS"); return
   account_id=str(accounts[0][0])
  stage="lookup_agent"
  agent=conn.execute(text("SELECT a.tenant_id,a.app_id,a.scope,a.source,a.status AS agent_status,a.created_by,a.backing_app_id,p.maintainer,p.status AS app_status FROM agents a LEFT JOIN apps p ON p.id=a.app_id AND p.tenant_id=a.tenant_id WHERE a.id=:id"),{"id":agent_id}).mappings().first()
  if not agent:
   emit("STOP",reason="AGENT_NOT_FOUND"); return
  tenant_id=str(agent["tenant_id"])
  stage="lookup_workspace_membership"
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
 stage="read_rbac_roles"
 role_data=call("roles","GET","members/rbac-roles",params={"account_id":account_id})
 keys={"agent.manage","app.acl.view_layout","app.acl.edit","app.acl.test_and_run"}
 if role_data is not None:
  roles=role_data.get("roles") or []
  emit("roles",count=len(roles),shown=min(len(roles),6))
  for r in roles[:6]: emit("role",id=r.get("id"),role_tag=r.get("role_tag"),category=r.get("category"),permission_keys=sorted(keys.intersection(r.get("permission_keys") or [])))
 stage="read_whitelist"
 whitelist=call("whitelist","GET","apps/whitelist",params={"app_id":app_id})
 if whitelist is not None:
  ids=whitelist.get("account_ids")
  emit("whitelist",account_ids_present=isinstance(ids,list),count=len(ids) if isinstance(ids,list) else None,contains_account=account_id in ids if isinstance(ids,list) else None)
 stage="read_member_policy"
 policies=call("policies","GET","apps/user-access-policies",params={"app_id":app_id})
 if policies is not None:
  rows=[r for r in (policies.get("data") or []) if (r.get("account") or {}).get("account_id")==account_id]
  emit("policies",scope=policies.get("scope"),target_rows=len(rows),policy_keys=[p.get("policy_key") for r in rows for p in (r.get("access_policies") or [])][:8])
 stage="evaluate_permissions"
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
 frames=traceback.extract_tb(exc.__traceback__)
 frame=frames[-1] if frames else None
 emit("STOP",stage=stage,error=type(exc).__name__,file=os.path.basename(frame.filename) if frame else None,line=frame.lineno if frame else None,function=frame.name if frame else None)
PYCODE
