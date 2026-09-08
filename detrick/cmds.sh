#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08 16:10
# Context: Chat对照正常；Completion节点mode与提示词列表结构冲突。验证全新节点初始化/保存，而非继续重复旧节点字数。
# Cmds: 2 条
# 同一受影响环境直接粘贴。命令2用于临时Chatflow，须替换APP_ID；只读，不运行模型、不发布、不改库。

# 1. 核对实际前后端镜像是否混用版本；最多8行，不输出环境变量。
docker inspect $(docker-compose ps -q) | python3 -c '
import json,sys
for r in json.load(sys.stdin):
 c=r.get("Config",{}); s=c.get("Labels",{}).get("com.docker.compose.service","")
 if s in ("api","web","api_websocket","worker"):
  print(s+" image="+c.get("Image","")+" id="+r.get("Image","")[:23])
' | head -8

# 2. 只读临时应用草稿结构。编辑后、重进后可分别执行，输出model_mode、prompt_shape和测试标记是否存在。
APP_ID='REPLACE_WITH_TEMP_APP_UUID'
docker-compose exec -T api python - "$APP_ID" <<'PY'
import json,sys,uuid
from sqlalchemy import create_engine,text
from configs import dify_config
try: app_id=str(uuid.UUID(sys.argv[1]))
except (ValueError,IndexError):
 print("Replace APP_ID with the temporary Chatflow UUID");sys.exit(1)
try:
 engine=create_engine(dify_config.SQLALCHEMY_DATABASE_URI)
 with engine.connect() as c:
  c.execute(text("SET TRANSACTION READ ONLY"))
  c.execute(text("SET LOCAL statement_timeout = '10s'"))
  rows=c.execute(text("SELECT graph,updated_at FROM workflows WHERE app_id=:app AND version='draft' LIMIT 2"),{"app":app_id}).fetchall()
  if len(rows)!=1: print("draft_rows="+str(len(rows)));sys.exit(0)
  graph=json.loads(rows[0][0]) if isinstance(rows[0][0],str) else rows[0][0]
  print("draft_updated="+str(rows[0][1]))
  nodes=[n for n in graph.get("nodes",[]) if n.get("data",{}).get("type")=="llm"]
  for n in nodes[:8]:
   d=n["data"];p=d.get("prompt_template"); items=p if isinstance(p,list) else [p]
   texts=[x.get("text","") for x in items if isinstance(x,dict)]
   has_marker=any("DIAG_COMPLETION_20260908" in v for v in texts if isinstance(v,str))
   print("node="+str(n.get("id"))+" mode="+str(d.get("model",{}).get("mode"))+" shape="+type(p).__name__+" marker="+str(has_marker))
  if not nodes:print("NO_LLM_NODES")
  if len(nodes)>8:print("Additional nodes omitted")
  c.rollback()
except Exception as e:
 print("READ_FAILED="+type(e).__name__);sys.exit(1)
PY
