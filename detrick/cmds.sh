#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08
# Context: 查看/发布/访问配置检查通过，API与Enterprise RBAC同源且密钥一致；捕获原WebApp POST的拒绝上下文。
# Cmds: 2 条

# 1. 在原部署目录当前终端执行，记录取证起点。然后在浏览器清空Network，重新打开权限设置并复现一次原失败操作。
# 请记录access-mode GET/POST各自状态，以及POST时间/响应中的request-id或trace-id（若有），不复制Cookie/Authorization。
DETRICK_WEBAPP_SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "capture_since=$DETRICK_WEBAPP_SINCE"

# 2. 复现后在同一终端执行。仅采集起点之后的Enterprise/RBAC日志，输出最后20条相关结构化摘要，不打印原始日志。
# 本轮不再运行check-access，避免与浏览器原请求混淆。无记录不等于没有权限检查。
docker-compose logs --no-color --timestamps --since "${DETRICK_WEBAPP_SINCE:?先执行命令1并复现}" --tail=600 dify-enterprise dify-enterprise-rbac 2>&1 | python3 -c '
import sys,json,re
from collections import deque
out=deque(maxlen=20); total=0; parsed=0; matched=0; unparsed=0
keys={"ts","timestamp","caller","trace_id","traceId","request_id","requestId","span_id","tenant_id","tenantId","account_id","accountId","resource_id","resourceId","resource_type","scene","account_role_ids","matched_role_ids","status","code","method","operation","path","route","reason"}
markers=("access-mode","unauthorized","whitelist","check-access denied","permission denied")
def fields(x,dst):
 if not isinstance(x,dict):return
 for k,v in x.items():
  if k in keys and isinstance(v,(str,int,bool,list)):
   if k in ("path","route"):v=str(v).split("?",1)[0]
   if k=="reason" and not re.fullmatch(r"[A-Za-z0-9_ .:-]{1,180}",str(v)):v="REASON_REDACTED"
   dst[k]=v[:8] if isinstance(v,list) else str(v)[:180]
  elif isinstance(v,dict):fields(v,dst)
for line in sys.stdin:
 total+=1; low=line.lower(); flags=[m for m in markers if m in low]
 start=line.find("{"); obj=None
 if start>=0:
  try:obj=json.JSONDecoder().raw_decode(line[start:])[0]
  except ValueError:pass
 d={};fields(obj,d)
 if obj is not None:parsed+=1
 if not flags and d.get("status")!="401" and d.get("code")!="401":continue
 matched+=1
 if obj is None:unparsed+=1
 prefix=line.split("|",1)[0]
 service="rbac" if "rbac" in prefix else "enterprise"
 d["source"]=service;d["markers"]=flags;d["structured"]=obj is not None
 if not d.get("ts") and not d.get("timestamp"):
  t=re.search(r"\d{4}-\d{2}-\d{2}T[0-9:.]+Z",line)
  if t:d["ts"]=t.group(0)
 out.append(d)
print(json.dumps({"input_lines":total,"parsed_json":parsed,"matched":matched,"unparsed_matches":unparsed,"shown":len(out)}))
for d in out:print(json.dumps(d,ensure_ascii=True))
'
