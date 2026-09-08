#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08 22:04
# Context: admin读取他人Agent返回403；API已启用RBAC、接口检查APP_VIEW_LAYOUT，日志NO_MATCH。本轮直接检查目标授权。
# Cmds: 2 条（设置目标 + 只读检查；预期输出约9行）
# 在Compose目录的同一个原shell中依次粘贴；不需要Token，不修改角色/白名单/数据库。

# 1. 输入目标Agent ID与当前登录账号ID。Agent ID取失败URL，账号ID取account/profile响应的id；输出最多1行。
read -r -p 'Agent UUID: ' DTR_AGENT_ID; read -r -p 'Current account UUID: ' DTR_ACCOUNT_ID

# 2. 自动解析Agent所属工作空间和授权App，核对角色、白名单、成员策略，并检查三个权限点；最多30行。
# 普通API服务按现有Compose为api；若真实名称不同，只替换下面的api。
# 日志中的新增拒绝可能由本探针产生，不能冒充刚才浏览器请求的原始日志。
docker-compose exec -T -e DTR_AGENT_ID="$DTR_AGENT_ID" -e DTR_ACCOUNT_ID="$DTR_ACCOUNT_ID" api python - <<'PYCODE' | tail -30
import os,json,logging
from uuid import UUID
logging.disable(logging.CRITICAL)
def emit(kind, **data): print(json.dumps({"check":kind,**data},ensure_ascii=True,default=str))
def main():
 from configs import dify_config
 from sqlalchemy import create_engine,text
 from services.enterprise.base import EnterpriseRequest
 agent_id=str(UUID(os.environ["DTR_AGENT_ID"]))
 account_id=str(UUID(os.environ["DTR_ACCOUNT_ID"]))
 # 只执行SELECT；显式只读事务，不调用App工厂或创建/修复Agent会话。
 engine=create_engine(dify_config.SQLALCHEMY_DATABASE_URI)
 with engine.connect() as conn:
  conn.execute(text("SET TRANSACTION READ ONLY"))
  agent=conn.execute(text("SELECT a.tenant_id,a.app_id,a.scope,a.backing_app_id,p.maintainer,p.status AS app_status FROM agents a LEFT JOIN apps p ON p.id=a.app_id AND p.tenant_id=a.tenant_id WHERE a.id=:id"),{"id":agent_id}).mappings().first()
  if not agent:
   emit("STOP",reason="AGENT_NOT_FOUND"); return
  tenant_id=str(agent["tenant_id"])
  member=conn.execute(text("SELECT role FROM tenant_account_joins WHERE tenant_id=:t AND account_id=:a"),{"t":tenant_id,"a":account_id}).first()
  app_id=str(agent["app_id"]) if agent["app_id"] else None
  emit("target",agent_id=agent_id,account_id=account_id,tenant_id=tenant_id,authz_app_id=app_id,scope=agent["scope"],has_separate_backing_app=bool(agent["backing_app_id"] and str(agent["backing_app_id"])!=app_id),is_maintainer=str(agent["maintainer"])==account_id,app_status=agent["app_status"],in_workspace=member is not None,legacy_role=member[0] if member else None)
  if not member or not app_id:
   emit("STOP",reason="MEMBER_OR_AUTHZ_APP_MISSING"); return
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
 keys={"agent.manage","app.acl.view_layout","app.acl.edit"}
 if role_data is not None:
  roles=role_data.get("roles") or []
  emit("roles",count=len(roles),items=[{"id":r.get("id"),"role_tag":r.get("role_tag"),"category":r.get("category"),"relevant_permission_keys":sorted(keys.intersection(r.get("permission_keys") or []))} for r in roles[:6]])
 whitelist=call("whitelist","GET","apps/whitelist",params={"app_id":app_id})
 if whitelist is not None:
  ids=whitelist.get("account_ids")
  emit("whitelist",account_ids_present=isinstance(ids,list),count=len(ids) if isinstance(ids,list) else None,contains_account=account_id in ids if isinstance(ids,list) else None)
 policies=call("policies","GET","apps/user-access-policies",params={"app_id":app_id})
 if policies is not None:
  rows=[r for r in (policies.get("data") or []) if (r.get("account") or {}).get("account_id")==account_id]
  emit("policies",scope=policies.get("scope"),target_rows=len(rows),policy_keys=[p.get("policy_key") for r in rows for p in (r.get("access_policies") or [])][:8])
 for scene in ("agent_manage","app_view_layout","app_edit"):
  payload={"tenant_id":tenant_id,"account_id":account_id,"scene":scene}
  if scene!="agent_manage": payload.update(resource_type="app",resource_id=app_id)
  data=call(scene,"POST","check-access",json=payload)
  if data is not None:
   summary={k:data[k] for k in ("allowed","reason","matched_role_ids","account_role_ids","whitelist_denial") if k in data}
   emit(scene,allowed_present="allowed" in data,**summary)
try:
 main()
except Exception as exc:
 emit("STOP",error=type(exc).__name__)
PYCODE
