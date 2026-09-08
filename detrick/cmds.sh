#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08
# Context: 回传库名/已显示凭据比较一致，未支持新增 RBAC 连默认库假设。shared.env 仅发现缺许可证显示变量。补齐截断的 RBAC 路由/企业配置；只读。
# Cmds: 2 条
# 只需异常环境，在 Compose 目录逐条完整粘贴执行；无需 source，不改配置。
# 输出短 JSON；请保留 true/false、path 和 base_path 原样。

# 1. API/worker 的 RBAC 路径是否确实为 /inner/api（最多 2 行）
docker inspect $(docker-compose ps -q api worker) | python3 -c '
import json,sys
from urllib.parse import urlsplit
for o in json.load(sys.stdin)[:2]:
    e=dict(x.split("=",1) for x in o["Config"].get("Env",[]) if "=" in x)
    svc=(o["Config"].get("Labels") or {}).get("com.docker.compose.service",o["Name"])
    u=urlsplit(e.get("ENTERPRISE_RBAC_API_URL",""))
    print(json.dumps({"service":svc,"path":u.path,"path_ok":u.path=="/inner/api",
          "target_ok":u.hostname=="dify-enterprise-rbac" and u.port==8086,
          "timeout":e.get("ENTERPRISE_RBAC_REQUEST_TIMEOUT")}))
'

# 2. 补齐企业后端的 RBAC 基地址、同步/迁移配置及上轮截断的凭据比较（最多 3 行；不输出凭据）
docker inspect $(docker-compose ps -q api dify-enterprise dify-enterprise-rbac) | python3 -c '
import json,sys
from urllib.parse import urlsplit
envs={}
for o in json.load(sys.stdin):
    svc=(o["Config"].get("Labels") or {}).get("com.docker.compose.service",o["Name"])
    envs[svc]=dict(x.split("=",1) for x in o["Config"].get("Env",[]) if "=" in x)
e=envs.get("dify-enterprise",{})
u=urlsplit(e.get("RBAC_INNER_BASE_URL",""))
print(json.dumps({"service":"dify-enterprise","base_present":bool(e.get("RBAC_INNER_BASE_URL")),
      "target_ok":u.hostname=="dify-enterprise-rbac" and u.port==8086,"base_path":u.path,
      "migration":e.get("MIGRATION_ENABLED"),"cron":e.get("WORKSPACE_SYNC_CRON"),
      "sync_timeout":e.get("WORKSPACE_SYNC_TIMEOUT")}))
def same(a,b,key):
    x,y=envs.get(a,{}).get(key),envs.get(b,{}).get(key)
    return "missing_or_empty" if not x or not y else "equal" if x==y else "different"
print(json.dumps({"api_enterprise_secret":same("api","dify-enterprise","ENTERPRISE_API_SECRET_KEY"),
      "enterprise_rbac_db_password":same("dify-enterprise","dify-enterprise-rbac","ENTERPRISE_DB_PASS")}))
'
