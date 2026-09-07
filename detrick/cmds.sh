#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 23:44
# Context: 正常环境也是新增 Agent；已回传关键源码一致；异常 worker 已订阅 app_rbac。优先比较有效配置和任务执行错误，尚未定位环境差异。
# Cmds: 3 条
# 在两套环境各自的 Compose 目录，把每条命令完整粘贴到平时 docker-compose 可用的终端执行。
# 无需 source，无需 export，无需改 PATH；不再从 Python 启动 docker-compose。

# 1. 两套都执行：镜像、RBAC 开关、路由、数据库及 API/worker 配置一致性（最多 25 行，凭据不输出）
docker inspect $(docker-compose ps -q api worker dify-enterprise-rbac dify-enterprise) | python3 -c '
import json,sys
from urllib.parse import urlsplit
try: objects=json.load(sys.stdin)
except ValueError:
    print("INSPECT_FAILED: container metadata was not received"); raise SystemExit(0)
def endpoint(v):
    if not v: return "<unset>"
    try:
        u=urlsplit(v if "://" in v else "//"+v)
        return (u.scheme+"://" if u.scheme else "")+str(u.hostname)+(":"+str(u.port) if u.port else "")
    except ValueError: return "<unparseable>"
envs={}
for o in objects[:8]:
    svc=(o["Config"].get("Labels") or {}).get("com.docker.compose.service",o["Name"])
    e=dict(x.split("=",1) for x in o["Config"].get("Env",[]) if "=" in x)
    envs.setdefault(svc,e)
    print("IMAGE",svc,o["Config"]["Image"],"id="+o["Image"])
    print("CONFIG",svc,"RBAC="+e.get("RBAC_ENABLED","<unset>"),
          "ENTERPRISE="+e.get("ENTERPRISE_ENABLED","<unset>"),
          "rbac_target="+endpoint(e.get("ENTERPRISE_RBAC_API_URL") or e.get("RBAC_INNER_BASE_URL")),
          "db_host="+endpoint(e.get("DB_HOST")),"db_name="+e.get("DB_DATABASE",e.get("DB_NAME","<unset>")))
a,w=envs.get("api",{}),envs.get("worker",{})
for group,keys in [
 ("routing",["ENTERPRISE_API_URL","ENTERPRISE_RBAC_API_URL","RBAC_ENABLED","DB_HOST","DB_PORT","DB_DATABASE","DB_USERNAME"]),
 ("broker",["CELERY_BROKER_URL","CELERY_QUEUES","REDIS_HOST","REDIS_PORT","REDIS_DB"]),
 ("credentials",["ENTERPRISE_API_SECRET_KEY","DB_PASSWORD","REDIS_PASSWORD"])]:
    print("API_WORKER_COMPARE",group," ".join(k+":"+("both-unset" if k not in a and k not in w else "equal" if a.get(k)==w.get(k) else "DIFFERENT") for k in keys))
'

# 2. 只需正常环境执行：确认实际授权队列；直接调用容器 Python 模块，绕开宿主函数与 celery 可执行文件查找问题（最多 10 行）
docker-compose exec -T worker python -m celery -A app.celery inspect active_queues --timeout=5 --json 2>&1 | python3 -c '
import json,sys
stream=sys.stdin.read(); decoder=json.JSONDecoder(); found=None
for i,ch in enumerate(stream):
    if ch!="{": continue
    try: obj,end=decoder.raw_decode(stream[i:])
    except ValueError: continue
    if isinstance(obj,dict) and obj and all(isinstance(v,list) and all(isinstance(q,dict) and "name" in q for q in v) for v in obj.values()):
        found=obj; break
if found is not None:
    for name,queues in list(found.items())[:8]:
        print("ACTIVE_QUEUE",name,"app_rbac="+str(any(q["name"]=="app_rbac" for q in queues)),"count="+str(len(queues)))
else:
    hints=[x for x in ["no nodes replied","no module named","no such option","unable to load celery application","connection refused","authentication","timed out","not found"] if x in stream.lower()]
    print("QUEUE_UNRESOLVED","bytes="+str(len(stream)),"hints="+str(hints))
    print("No subscription conclusion can be drawn.")
'

# 3. 两套都执行：近 24 小时初始化任务/创建者授权同步结果（每服务最多 8 行；日志缺失不代表任务没有执行）
for svc in api worker; do
  echo "[authorization task logs $svc]"
  docker-compose logs --since 24h --tail=2000 --no-color "$svc" 2>&1 |
    grep -iE "initialize_created_app_rbac_access_task|Failed to initialize app RBAC|Failed to sync.*creator|sync.creator.*failed|unregistered task.*rbac" |
    sed -E "s/((token|password|secret|authorization)[\" ]*[:=][\" ]*)[^ ,}]+/\1[REDACTED_SECRET]/Ig" |
    tail -8 | cut -c1-1400
done
