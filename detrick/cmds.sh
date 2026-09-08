#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08
# Context: 现场API运行/Compose均RBAC=true，Enterprise运行/Compose均UNSET。修复Enterprise配置缺失，再验证WebApp写权限。
# Cmds: 2 条
# 先编辑当前docker-compose实际使用的Compose文件：找到镜像为dify-ee-enterprise的服务，在已有environment映射下增加：
#   RBAC_ENABLED: "true"
# 不重复创建environment键，不改api或独立rbac服务，不修改数据库角色。
# 若已有environment是列表格式，则追加列表项：- RBAC_ENABLED=true
# 保存前保留原文件副本以便回退；只新增上述一个配置项。
# 下列命令在原部署目录同一终端分别粘贴，不使用source，不需要在新bash中调用docker-compose。

# 1. 只读核验合并后的API/Enterprise均开启RBAC，并从Enterprise镜像识别真实Compose服务名，避免名称拼写差异。
DETRICK_ENTERPRISE_SERVICE=$(docker-compose config 2>/dev/null | docker-compose exec -T api python -c '
import sys
try:
 import yaml
 d=yaml.safe_load(sys.stdin)
 if not isinstance(d,dict) or not isinstance(d.get("services"),dict):raise ValueError("CONFIG_UNAVAILABLE")
 services=d["services"]
 matches=[(k,v) for k,v in services.items() if str(v.get("image","")).split("@",1)[0].rsplit("/",1)[-1].split(":",1)[0]=="dify-ee-enterprise"]
 if len(matches)!=1:raise ValueError("EXPECTED_ONE_ENTERPRISE_SERVICE")
 name,enterprise=matches[0]
 def enabled(service):
  env=service.get("environment") or {}
  if isinstance(env,list):env=dict((x.split("=",1)+[None])[:2] for x in env)
  return str(env.get("RBAC_ENABLED","")).lower() in ("true","1")
 if not enabled(services.get("api",{})):raise ValueError("API_RBAC_NOT_TRUE")
 if not enabled(enterprise):raise ValueError("ENTERPRISE_RBAC_NOT_TRUE_CHECK_EDITED_CONFIG")
 print(name)
except ValueError as e:
 allowed={"CONFIG_UNAVAILABLE","EXPECTED_ONE_ENTERPRISE_SERVICE","API_RBAC_NOT_TRUE","ENTERPRISE_RBAC_NOT_TRUE_CHECK_EDITED_CONFIG"}
 print(str(e) if str(e) in allowed else "CONFIG_PARSE_FAILED",file=sys.stderr);sys.exit(1)
except Exception as e:
 print("CONFIG_READ_FAILED="+type(e).__name__,file=sys.stderr);sys.exit(1)
')
if [ -n "$DETRICK_ENTERPRISE_SERVICE" ]; then
  printf 'CONFIG_READY service=%s RBAC_ENABLED=true
' "$DETRICK_ENTERPRISE_SERVICE"
else
  echo 'STOP: 配置未通过检查，不执行命令2'
fi

# 2. 仅在命令1输出CONFIG_READY后执行。重建Enterprise服务会造成该服务短暂不可用；不重建API/worker/RBAC。
# 使用up重建以加载新环境变量，单纯restart不会加载；输出最多12行启动日志和4行容器状态。
if [ -z "${DETRICK_ENTERPRISE_SERVICE:-}" ]; then
  echo 'STOP: 先修正配置并通过命令1'
elif (set -o pipefail; docker-compose up -d --no-deps --no-build --force-recreate "$DETRICK_ENTERPRISE_SERVICE" 2>&1 | tail -12); then
  docker inspect $(docker-compose ps -q "$DETRICK_ENTERPRISE_SERVICE") | python3 -c '
import sys,json
rows=json.load(sys.stdin)
if not rows:print("NO_ENTERPRISE_CONTAINER");sys.exit(1)
for r in rows[:4]:
 c=r.get("Config") or {};s=r.get("State") or {};e=dict(x.split("=",1) for x in c.get("Env",[]) if "=" in x)
 value=e.get("RBAC_ENABLED");value=value if value in ("true","false","True","False","1","0") else "UNSET_OR_OTHER"
 print(json.dumps({"service":(c.get("Labels") or {}).get("com.docker.compose.service"),"status":s.get("Status"),"health":(s.get("Health") or {}).get("Status","NO_HEALTHCHECK"),"RBAC_ENABLED":value}))
'
else
  echo 'RECREATE_FAILED: 请回传以上错误摘要'
fi
# 容器running且RBAC_ENABLED=true后，在原账号/原workspace/原app复测POST access-mode。
# 若成功，退出重进确认所选访问范围保留。回传POST状态及持久化结果；容器running不是业务验收成功。
