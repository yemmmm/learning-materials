#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08
# Context: Enterprise写方法401，三项API RBAC判定允许；本机3.12.0静态证据显示Enterprise自身RBAC_ENABLED未设时退回传统角色。确认现场与Compose有效配置。
# Cmds: 2 条
# 在原部署目录当前终端粘贴；只读，不重启，不改变授权。

# 1. 当前API/Enterprise容器的RBAC开关，输出最多4行（不输出其他环境变量）。
docker inspect $(docker-compose ps -q api dify-enterprise) | python3 -c '
import sys,json
rows=json.load(sys.stdin)
if not rows:print("NO_CONTAINERS");sys.exit(1)
for r in rows[:4]:
 c=r.get("Config") or {};e=dict(x.split("=",1) for x in c.get("Env",[]) if "=" in x)
 v=e.get("RBAC_ENABLED");v=v if v in ("true","false","True","False","TRUE","FALSE","1","0","") else "UNSET" if v is None else "INVALID_VALUE"
 print(json.dumps({"source":"running_container","service":(c.get("Labels") or {}).get("com.docker.compose.service"),"image_tag":c.get("Image","").rsplit(":",1)[-1],"RBAC_ENABLED":v}))
'

# 2. Compose合并后的有效RBAC配置，仅解析指定字段，不输出完整Compose（可能含凭据）。输出最多2行。
# 必须仍在同一部署目录；本条不启动应用，仅在现有API容器内用PyYAML解析stdin。
docker-compose config 2>/dev/null | docker-compose exec -T api python -c '
import sys,json
try:
 import yaml
 d=yaml.safe_load(sys.stdin)
 if not isinstance(d,dict) or not isinstance(d.get("services"),dict):
  print("COMPOSE_CONFIG_UNAVAILABLE");sys.exit(1)
 for service in ("api","dify-enterprise"):
  cfg=d["services"].get(service)
  if cfg is None:print(service+" SERVICE_MISSING");continue
  env=cfg.get("environment") or {}
  if isinstance(env,list):env=dict((x.split("=",1)+[None])[:2] for x in env)
  v=env.get("RBAC_ENABLED");state="UNSET" if "RBAC_ENABLED" not in env else "NULL" if v is None else str(v)
  if state not in ("UNSET","NULL","true","false","True","False","TRUE","FALSE","1","0",""):state="INVALID_VALUE"
  print(json.dumps({"source":"compose_resolved","service":service,"RBAC_ENABLED":state}))
except Exception as e:
 print("CONFIG_READ_FAILED="+type(e).__name__);sys.exit(1)
'
