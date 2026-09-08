#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08
# Context: 草稿/当前发布版提示词长度缺行；拒绝日志属于其他app。补齐目标app快照并核对实际保存权限源码，只读。
# Cmds: 2 条
# 在上轮同一环境、同一终端逐块完整复制执行；不需要再次编辑或发布。
# 已知环境及问题状态见 environment.md、issues.md。

# 1. 查询上轮同一应用：短行明确标识 draft/current/older，避免错行；最多29行。
APP_ID='43c6d3bb-170c-478e-a53c-64c48e1668aa'
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
   label="draft" if r["version"]=="draft" else ("current" if str(r["id"])==str(app["workflow_id"]) else "older")
   print("SNAPSHOT "+label+" updated="+str(r["updated_at"])+" llm_nodes="+str(len(nodes)))
   for n in nodes[:5]:
    data=n.get("data",{}); prompt=data.get("prompt_template")
    print("PROMPT "+label+" node="+str(n.get("id"))+" chars="+str(prompt_chars(prompt))+" type="+type(prompt).__name__)
   if len(nodes)>5: print("Additional LLM nodes omitted: "+str(len(nodes)-5))
  if not rows: print("NO_WORKFLOW_SNAPSHOTS")
  conn.rollback()
except Exception as e:
 print("READ_FAILED type="+type(e).__name__+" (details omitted to protect credentials)"); sys.exit(1)
PY

# 2. 读取API保存/发布的实际鉴权装饰器及文件指纹；不启动应用、不调用接口。
docker-compose exec -T api python - <<'PY'
import ast,hashlib,pathlib
p=pathlib.Path("controllers/console/app/workflow.py")
if not p.exists():
 print("SOURCE_NOT_FOUND"); raise SystemExit(0)
s=p.read_text();print("workflow_controller sha256="+hashlib.sha256(s.encode()).hexdigest()[:16])
tree=ast.parse(s)
for cls in tree.body:
 if not isinstance(cls,ast.ClassDef): continue
 routes=[x.value for dec in cls.decorator_list for x in ast.walk(dec) if isinstance(x,ast.Constant) and isinstance(x.value,str)]
 if not any(x.endswith(("/workflows/draft","/workflows/publish")) for x in routes): continue
 for fn in cls.body:
  if not isinstance(fn,ast.FunctionDef) or fn.name not in ("get","post"): continue
  perms=sorted(set(x.attr for d in fn.decorator_list for x in ast.walk(d) if isinstance(x,ast.Attribute) and x.attr.startswith("APP_")))
  print(cls.name+"."+fn.name+" permissions="+(",".join(perms) or "none_in_decorators"))
PY
