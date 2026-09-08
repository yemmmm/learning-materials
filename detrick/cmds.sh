#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08 14:45
# Context: 实际草稿GET/POST均检查APP_VIEW_LAYOUT，发布POST检查APP_RELEASE_AND_VERSION；草稿和当前版提示词长度仍缺行。本轮各输出一行。
# Cmds: 2 条
# 同一环境同一终端完整粘贴；只读固定app，不编辑、不发布。UNKNOWN不代表空提示词。

# 1. 草稿：只输出一行状态和提示词总长度，不输出正文。
docker-compose exec -T api python - DRAFT <<'PY'
import json,sys
from sqlalchemy import create_engine,text
from configs import dify_config
label=sys.argv[1]
try:
 engine=create_engine(dify_config.SQLALCHEMY_DATABASE_URI)
 with engine.connect() as c:
  c.execute(text("SET TRANSACTION READ ONLY"))
  c.execute(text("SET LOCAL statement_timeout = '10s'"))
  condition="w.version='draft'" if label=="DRAFT" else "w.id=a.workflow_id"
  rows=c.execute(text("SELECT w.graph FROM workflows w JOIN apps a ON a.id=w.app_id AND a.tenant_id=w.tenant_id WHERE a.id=:app AND "+condition+" LIMIT 2"),{"app":"43c6d3bb-170c-478e-a53c-64c48e1668aa"}).fetchall()
  if len(rows)!=1:
   print(label+" snapshot_rows="+str(len(rows))); sys.exit(0)
  graph=json.loads(rows[0][0]) if isinstance(rows[0][0],str) else rows[0][0]
  nodes=[n for n in graph.get("nodes",[]) if n.get("id")=="llm"]
  if len(nodes)!=1:
   print(label+" target_llm_nodes="+str(len(nodes))); sys.exit(0)
  data=nodes[0].get("data",{}); p=data.get("prompt_template")
  items=p if isinstance(p,list) else [p]
  lengths=[len(x) if isinstance(x,str) else len(x["text"]) if isinstance(x,dict) and isinstance(x.get("text"),str) else None for x in items]
  total=sum(lengths) if all(v is not None for v in lengths) else "UNKNOWN"
  state=type(p).__name__ if "prompt_template" in data else "MISSING"
  print(label+" prompt="+state+" items="+str(len(items))+" chars="+str(total))
  c.rollback()
except Exception as e:
 print(label+" READ_FAILED="+type(e).__name__); sys.exit(1)
PY

# 2. 当前发布版：只输出一行状态和提示词总长度，不输出正文。
docker-compose exec -T api python - CURRENT <<'PY'
import json,sys
from sqlalchemy import create_engine,text
from configs import dify_config
label=sys.argv[1]
try:
 engine=create_engine(dify_config.SQLALCHEMY_DATABASE_URI)
 with engine.connect() as c:
  c.execute(text("SET TRANSACTION READ ONLY"))
  c.execute(text("SET LOCAL statement_timeout = '10s'"))
  condition="w.version='draft'" if label=="DRAFT" else "w.id=a.workflow_id"
  rows=c.execute(text("SELECT w.graph FROM workflows w JOIN apps a ON a.id=w.app_id AND a.tenant_id=w.tenant_id WHERE a.id=:app AND "+condition+" LIMIT 2"),{"app":"43c6d3bb-170c-478e-a53c-64c48e1668aa"}).fetchall()
  if len(rows)!=1:
   print(label+" snapshot_rows="+str(len(rows))); sys.exit(0)
  graph=json.loads(rows[0][0]) if isinstance(rows[0][0],str) else rows[0][0]
  nodes=[n for n in graph.get("nodes",[]) if n.get("id")=="llm"]
  if len(nodes)!=1:
   print(label+" target_llm_nodes="+str(len(nodes))); sys.exit(0)
  data=nodes[0].get("data",{}); p=data.get("prompt_template")
  items=p if isinstance(p,list) else [p]
  lengths=[len(x) if isinstance(x,str) else len(x["text"]) if isinstance(x,dict) and isinstance(x.get("text"),str) else None for x in items]
  total=sum(lengths) if all(v is not None for v in lengths) else "UNKNOWN"
  state=type(p).__name__ if "prompt_template" in data else "MISSING"
  print(label+" prompt="+state+" items="+str(len(items))+" chars="+str(total))
  c.rollback()
except Exception as e:
 print(label+" READ_FAILED="+type(e).__name__); sys.exit(1)
PY
