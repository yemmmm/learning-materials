#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08
# Context: admin访问他人Agent，GET /console/api/agent/<id>/chat-messages返回403；核对APP_VIEW_LAYOUT检查及本次拒绝。
# Cmds: 3 条（只读，每条最多30行）
# 在原Compose目录直接粘贴到当前shell；不要新开bash运行，docker-compose可能是shell函数。

# 1. 核对实际API服务版本和RBAC开关；回传未包含普通api服务，不据此判断它不存在。最多10行，不输出私有仓库地址。
docker-compose ps -q | xargs -r docker inspect | python3 -c '
import json,sys
rows=json.load(sys.stdin)
count=0
for row in rows:
 c=row.get("Config",{}); name=c.get("Labels",{}).get("com.docker.compose.service","")
 if "api" not in name: continue
 env=dict(x.split("=",1) for x in c.get("Env",[]) if "=" in x)
 print(json.dumps({"service":name,"image":c.get("Image","").rsplit("/",1)[-1],"RBAC_ENABLED":env.get("RBAC_ENABLED","UNSET"),"ENTERPRISE_ENABLED":env.get("ENTERPRISE_ENABLED","UNSET")}))
 count+=1
 if count>=10: break
'

# 2. 从已确认的api_websocket镜像核对该接口装饰器；这是同镜像代码证据，不证明HTTP路由由它承接。最多27行。
docker-compose exec -T api_websocket python - <<'PYCODE'
from pathlib import Path
p=Path("/app/api/controllers/console/app/message.py")
if not p.exists():
 print("SOURCE_NOT_FOUND: /app/api/controllers/console/app/message.py")
else:
 lines=p.read_text().splitlines()
 for i,line in enumerate(lines):
  if "class AgentChatMessageListApi" in line:
   print("FILE="+str(p))
   for j in range(max(0,i-1),min(len(lines),i+25)): print(str(j+1)+":"+lines[j])
   break
 else: print("HANDLER_NOT_FOUND: AgentChatMessageListApi")
PYCODE

# 3. 重新打开目标Agent触发403后立即执行；提取最近3分钟权限字段，最多10条，不输出业务正文或认证头。
docker-compose logs --no-color --since=3m --tail=150 dify-enterprise-rbac 2>&1 | python3 -c '
import sys,re,json
keys="scene|reason|account_id|tenant_id|resource_id|resource_type|account_role_ids|matched_role_ids|whitelist_denial|allowed"
q=chr(34)
pattern=re.compile(q+"("+keys+")"+q+r"\s*:\s*(\[[^\]]*\]|"+q+r"[^"+q+r"]*"+q+r"|true|false|null)")
rows=[]
for line in sys.stdin:
 if not re.search(r"denied|whitelist_denial|unauthorized|forbidden",line,re.I): continue
 fields={k:json.loads(v) for k,v in pattern.findall(line)}
 if fields: rows.append(fields)
for row in rows[-10:]: print(json.dumps(row,ensure_ascii=True))
if not rows: print("NO_MATCH: no extracted RBAC denial; check service name and failed browser request path/status.")
'
