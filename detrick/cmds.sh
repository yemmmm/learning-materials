#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08
# Context: 部分 workspace 的 WebApp 权限操作401；LLM提示词发布后重进为空。分别取证，不回填权限、不改数据。
# Cmds: 3 条
# 在一套受影响环境的 Compose 目录逐块完整粘贴到已有 docker-compose 函数的终端。
# 命令2前点击一次401权限按钮；命令3先替换APP_ID。无需重新编辑或发布工作流。

# 1. 镜像、WebSocket地址、API/WebSocket数据源一致性；仅输出选定字段。
docker inspect $(docker-compose ps -q) | python3 -c '
import json,sys
from urllib.parse import urlsplit
services={}
for row in json.load(sys.stdin):
 c=row.get("Config",{}); name=c.get("Labels",{}).get("com.docker.compose.service","")
 if name not in ("api","web","api_websocket","dify-enterprise","dify-enterprise-rbac"): continue
 env=dict(x.split("=",1) for x in c.get("Env",[]) if "=" in x); services[name]=env
 print(json.dumps({"service":name,"image":c.get("Image"),"running":row.get("State",{}).get("Running")}))
 if name in ("api","api_websocket"): print(json.dumps({"service":name,"RBAC_ENABLED":env.get("RBAC_ENABLED","<unset>"),"ENTERPRISE_ENABLED":env.get("ENTERPRISE_ENABLED","<unset>")}))
 if name=="web":
  u=urlsplit(env.get("NEXT_PUBLIC_SOCKET_URL","")); print(json.dumps({"socket_scheme":u.scheme,"socket_host":u.hostname,"socket_path":u.path}))
a=services.get("api",{}); w=services.get("api_websocket",{})
print(json.dumps({"api_websocket_present":bool(w)}))
if a and w:
 for label,keys in [("database",["DB_HOST","DB_PORT","DB_DATABASE","DB_USERNAME","DB_PASSWORD"]),("redis",["REDIS_HOST","REDIS_PORT","REDIS_DB","REDIS_USERNAME","REDIS_PASSWORD","REDIS_USE_SSL"]),("auth",["SECRET_KEY","ENTERPRISE_API_SECRET_KEY","ENTERPRISE_RBAC_API_URL"])]:
  print(json.dumps({"compare":label,"different_keys":[k for k in keys if a.get(k)!=w.get(k)],"both_unset":[k for k in keys if k not in a and k not in w]}))
' | head -18

# 2. 最近15分钟RBAC拒绝元数据，最多12条；不输出原始日志、令牌或提示词。
docker-compose logs --no-color --since 15m --tail 800 dify-enterprise-rbac 2>&1 | python3 -c '
import json,sys,collections
out=collections.deque(maxlen=12)
for line in sys.stdin:
 start=line.find("{")
 if start<0: continue
 try: d=json.loads(line[start:])
 except ValueError: continue
 a=d.get("attributes",{})
 if not isinstance(a,dict): continue
 if "denied" not in str(d.get("message","")).lower() and "whitelist" not in str(a.get("reason","")).lower(): continue
 allowed=("account_id","tenant_id","resource_id","resource_type","scene","account_role_ids","matched_role_ids")
 r={k:a[k] for k in allowed if k in a}; r["ts"]=d.get("ts"); r["whitelist_denial"]="whitelist" in str(a.get("reason","")).lower(); out.append(r)
for r in out: print(json.dumps(r))
if not out: print("NO_PARSED_RBAC_DENIAL: does not rule out enterprise/session authorization errors or unavailable logs")
' | head -12

# 3. 替换成提示词清空工作流地址栏的app UUID；只读草稿及最近发布快照，输出提示词长度，不输出正文。
APP_ID='REPLACE_WITH_WORKFLOW_APP_UUID'
docker-compose exec -T api python - "$APP_ID" <<'PY'
import json,sys,uuid
from sqlalchemy import create_engine,text
from configs import dify_config
try: app_id=str(uuid.UUID(sys.argv[1]))
except (ValueError,IndexError):
 print("Replace APP_ID with the affected workflow UUID first"); sys.exit(1)
def prompt_chars(p):
 if isinstance(p,str): return len(p)
 if isinstance(p,list):
  values=[prompt_chars(x) for x in p]
  return sum(values) if all(x is not None for x in values) else None
 if isinstance(p,dict): return len(p["text"]) if isinstance(p.get("text"),str) else None
 return None
try:
 engine=create_engine(dify_config.SQLALCHEMY_DATABASE_URI)
 with engine.connect() as conn:
  conn.execute(text("SET TRANSACTION READ ONLY"))
  conn.execute(text("SET LOCAL statement_timeout = '10s'"))
  app=conn.execute(text("SELECT id, tenant_id, mode, workflow_id FROM apps WHERE id=:app"),{"app":app_id}).mappings().first()
  if not app: print("APP_NOT_FOUND"); sys.exit(0)
  print(json.dumps({"app_id":app_id,"tenant_id":app["tenant_id"],"mode":app["mode"],"published_id":app["workflow_id"]},default=str))
  rows=conn.execute(text("SELECT id, version, created_at, updated_at, graph FROM workflows WHERE app_id=:app AND tenant_id=:tenant ORDER BY (version='draft') DESC, created_at DESC LIMIT 4"),{"app":app_id,"tenant":app["tenant_id"]}).mappings().all()
  for r in rows:
   graph=json.loads(r["graph"]) if isinstance(r["graph"],str) else r["graph"]
   nodes=[n for n in (graph or {}).get("nodes",[]) if n.get("data",{}).get("type")=="llm"]
   print(json.dumps({"workflow_id":r["id"],"version":r["version"],"current_published":str(r["id"])==str(app["workflow_id"]),"created_at":r["created_at"],"updated_at":r["updated_at"],"llm_nodes":len(nodes)},default=str))
   for n in nodes[:5]:
    data=n.get("data",{}); prompt=data.get("prompt_template")
    print(json.dumps({"node_id":n.get("id"),"prompt_present":"prompt_template" in data,"prompt_type":type(prompt).__name__,"prompt_chars":prompt_chars(prompt)}))
   if len(nodes)>5: print("Additional LLM nodes omitted: "+str(len(nodes)-5))
  if not rows: print("NO_WORKFLOW_SNAPSHOTS")
  conn.rollback()
except Exception as e:
 print("READ_FAILED type="+type(e).__name__+" (details omitted to protect credentials)"); sys.exit(1)
PY
