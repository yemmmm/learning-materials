#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08
# Context: 恢复WebApp access-mode 401。已先检索历史PR20785，暂不支持套用非企业版误请求修复；关联本次app、账号workspace关系和同期拒绝。
# Cmds: 2 条
# 同一受影响环境当前终端完整粘贴。只读、不回填权限。先替换APP_ID，并确认ACCOUNT_ID是本次登录账号。

# 1. 只读目标app和指定账号的workspace成员关系；传统role不等于RBAC有效角色。
APP_ID='REPLACE_WITH_FAILED_APP_UUID'
ACCOUNT_ID='dc81582c-3934-4d8f-b034-9cb7809dce2b'
docker-compose exec -T api python - "$APP_ID" "$ACCOUNT_ID" <<'PY'
import sys,uuid,json
from sqlalchemy import create_engine,text
from configs import dify_config
try: app_id=str(uuid.UUID(sys.argv[1]));account_id=str(uuid.UUID(sys.argv[2]))
except (ValueError,IndexError): print('REPLACE_APP_ID_AND_CONFIRM_ACCOUNT_ID');sys.exit(1)
try:
 with create_engine(dify_config.SQLALCHEMY_DATABASE_URI).connect() as c:
  c.execute(text('SET TRANSACTION READ ONLY'))
  c.execute(text("SET LOCAL statement_timeout='10s'"))
  a=c.execute(text('SELECT id,tenant_id,mode FROM apps WHERE id=:app'),{'app':app_id}).mappings().first()
  if not a:print('APP_NOT_FOUND');sys.exit(0)
  print('app='+str(a['id']));print('workspace='+str(a['tenant_id']));print('app_mode='+str(a['mode']))
  r=c.execute(text('SELECT role,"current" AS is_current FROM tenant_account_joins WHERE tenant_id=:tenant AND account_id=:account'),{'tenant':a['tenant_id'],'account':account_id}).mappings().all()
  print('account='+account_id);print('membership_rows='+str(len(r)))
  for v in r[:2]:print(json.dumps({'stored_tenant_role':v['role'],'stored_current_workspace':v['is_current']}))
  print('NOTE stored role/current are not proof of effective RBAC permission or request token workspace')
  c.rollback()
except Exception as e:print('READ_FAILED='+type(e).__name__);sys.exit(1)
PY

# 2. 点击一次出错的WebApp权限按钮后执行。最近15分钟结构化拒绝元数据，最多12条，不输出原始日志/令牌。
docker-compose logs --no-color --since 15m --tail 800 dify-enterprise dify-enterprise-rbac 2>&1 | python3 -c '
import json,sys,re,collections
out=collections.deque(maxlen=12);parsed=0
for line in sys.stdin:
 i=line.find("{")
 if i<0:continue
 try:d=json.loads(line[i:])
 except ValueError:continue
 if not isinstance(d,dict):continue
 parsed+=1;a=d.get("attributes",{});a=a if isinstance(a,dict) else {};m=dict(d);m.update(a)
 message=str(m.get("message",m.get("msg","")));reason=str(m.get("reason",""));path=str(m.get("path",m.get("uri",m.get("url",""))))
 content=(message+" "+reason+" "+path).lower()
 if not any(x in content for x in ("access-mode","unauthorized","forbidden","denied")):continue
 row={"ts":str(m.get("ts",m.get("time","")))[:40],"source":"rbac" if "rbac" in line[:i].lower() else "enterprise"}
 for k in ("account_id","tenant_id","resource_id","app_id"):
  v=str(m.get(k,""))
  if re.match(r"^[0-9a-fA-F-]{36}$",v):row[k]=v
 for k in ("scene","resource_type","method","code","status"):
  v=str(m.get(k,""))
  if v and re.match(r"^[A-Za-z0-9_.-]{1,80}$",v):row[k]=v
 row["access_mode_request"]="access-mode" in content
 row["keywords"]=[x for x in ("unauthorized","forbidden","whitelist","permission","token","tenant") if x in content]
 out.append(row)
for r in out:print(json.dumps(r))
if not out:print("NO_MATCH parsed="+str(parsed)+"; no proof that authorization passed; need browser Response")
' | head -12
