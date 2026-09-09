#!/bin/bash
# === Detrick Targeted Agent Member Grant ===
# Time: 2026-09-09
# Context: 新版Agents无内容权限UI入口；本Agent指定成员名单未包含目标admin，查看/编辑均被白名单拒绝。
# Cmds: 2 条（设置账号 + 单成员授权并验证）
# 适用：本次EE 3.12.1、固定Agent及关联App、目标已有builtin admin角色、scope=specific。
# 重要：第2条会写入该账号在该App上的default（按角色权限）策略；不会给全员开放。
# 其他账号不变、角色不变、scope不变。发现目标已有自定义成员策略时停止，不覆盖。
# API服务用当前配置的内部RBAC接口及密钥；操作账号为输入邮箱解析出的admin本人，不冒用创建者。
# 数据库仅SELECT，授权通过与正式Console单成员API相同的RBAC服务接口写入。
# 在原Compose目录直接复制两个命令块到同一个现有shell；docker-compose可能是shell函数，不要新开bash执行。
# 单条输出最多30行；不输出邮箱、Cookie、Token或密钥。执行后还需实际打开Agent并保存一次编辑验证。

# 1. 输入此前排查的登录邮箱，也支持完整账号UUID；无须重新填写Agent ID。
read -r -p 'Current admin login email (or UUID): ' DTR_ACCOUNT_ID

# 2. 【写操作】只给本次固定Agent上的目标账号添加default策略，然后检查白名单、查看和编辑权限。
docker-compose exec -T -e DTR_ACCOUNT_ID="$DTR_ACCOUNT_ID" api python - <<'PYCODE' | tail -30
import os,json,logging
from uuid import UUID
logging.disable(logging.CRITICAL)
def emit(kind, **data): print(json.dumps({"check":kind,**data},ensure_ascii=True,default=str))
def main():
 from configs import dify_config
 from sqlalchemy import create_engine,text
 from services.enterprise.base import EnterpriseRequest
 agent_id="01a07f83-4f8b-7d24-b87b-1fa54a15dabe"
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
  agent=conn.execute(text("SELECT a.tenant_id,a.app_id,a.scope,a.backing_app_id,p.maintainer,p.status AS app_status FROM agents a LEFT JOIN apps p ON p.id=a.app_id AND p.tenant_id=a.tenant_id WHERE a.id=:id"),{"id":agent_id}).mappings().first()
  if not agent:
   emit("STOP",reason="AGENT_NOT_FOUND"); return
  tenant_id=str(agent["tenant_id"])
  member=conn.execute(text("SELECT role FROM tenant_account_joins WHERE tenant_id=:t AND account_id=:a"),{"t":tenant_id,"a":account_id}).first()
  app_id=str(agent["app_id"]) if agent["app_id"] else None
  emit("target",agent_id=agent_id,account_id=account_id,tenant_id=tenant_id,authz_app_id=app_id,scope=agent["scope"],has_separate_backing_app=bool(agent["backing_app_id"] and str(agent["backing_app_id"])!=app_id),is_maintainer=str(agent["maintainer"])==account_id,app_status=agent["app_status"],in_workspace=member is not None,legacy_role=member[0] if member else None)
  if not member or app_id!="92714548-25b2-4c14-85e9-11598059fa8e" or agent["scope"]!="roster" or agent["app_status"]!="normal":
   emit("STOP",reason="MEMBER_OR_FIXED_AGENT_APP_CHECK_FAILED"); return
 def call(method,endpoint,**kwargs):
  data=EnterpriseRequest.send_inner_rbac_request(method,"/rbac/"+endpoint,tenant_id=tenant_id,account_id=account_id,timeout=10,**kwargs)
  if not isinstance(data,dict): raise ValueError("Unexpected response type")
  return data
 roles=call("GET","members/rbac-roles",params={"account_id":account_id}).get("roles") or []
 if not any(r.get("role_tag")=="admin" and r.get("category")=="global_system_default" for r in roles):
  emit("STOP",reason="TARGET_IS_NOT_CONFIRMED_BUILTIN_ADMIN"); return
 before=call("GET","apps/user-access-policies",params={"app_id":app_id})
 if before.get("scope")!="specific":
  emit("STOP",reason="ACCESS_SCOPE_CHANGED"); return
 rows=[r for r in (before.get("data") or []) if (r.get("account") or {}).get("account_id")==account_id]
 policies=[p for r in rows for p in (r.get("access_policies") or [])]
 if any(p.get("policy_key")!="default" and p.get("id")!="default" for p in policies):
  emit("STOP",reason="EXISTING_CUSTOM_MEMBER_POLICY_PRESERVED"); return
 emit("change",app_id=app_id,account_id=account_id,scope="specific",add_policy="default",actor="same_admin_account")
 if policies:
  emit("write",result="SKIPPED_DEFAULT_ALREADY_ASSIGNED")
 else:
  # Same payload and endpoint used by RBACService.AppAccess.replace_user_access_policies.
  # One target account; never calls scope/whitelist replacement or role migration.
  call("PUT","apps/user-access-policies",params={"app_id":app_id,"account_id":account_id},json={"access_policy_ids":["default"],"account_ids":[]})
  emit("write",result="SINGLE_MEMBER_POLICY_ASSIGNED")
 after=call("GET","apps/user-access-policies",params={"app_id":app_id})
 whitelist=call("GET","apps/whitelist",params={"app_id":app_id})
 ids=whitelist.get("account_ids")
 contains=isinstance(ids,list) and account_id in ids
 emit("verify",scope=after.get("scope"),contains_account=contains)
 passed=after.get("scope")=="specific" and contains
 for scene in ("app_view_layout","app_edit"):
  result=call("POST","check-access",json={"tenant_id":tenant_id,"account_id":account_id,"scene":scene,"resource_type":"app","resource_id":app_id})
  emit(scene,allowed=result.get("allowed","MISSING"))
  if result.get("allowed") is not True:
   passed=False
   emit(scene,reason=result.get("reason","MISSING"))
 emit("result",status="PERMISSION_CHECKS_PASSED" if passed else "WRITTEN_OR_PRESENT_BUT_VERIFICATION_INCOMPLETE",next="Reopen Agent and verify an edit can be saved")
try:
 main()
except Exception as exc:
 emit("STOP",error=type(exc).__name__,status=getattr(exc,"status_code",None))
PYCODE
