#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-09
# Context: 为Agents页面成员统一开放Agent内容，安装代码补丁前核对现场模块；只读，不改白名单或服务。
# Cmds: 2条；在部署目录现有shell中分别粘贴，保留docker-compose函数。

# 1. 分别核对两个API服务的公共权限模块指纹；每个服务一行。
for DTR_SVC in api api_websocket; do
  printf '%s ' "$DTR_SVC"
  docker-compose exec -T "$DTR_SVC" python - <<'PYCODE'
import hashlib,json
from pathlib import Path
p=Path('/app/api/controllers/common/wraps.py')
print(json.dumps({'module':'controllers/common/wraps.py','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
PYCODE
done

# 2. 核对Agent数据模型和Console蓝图声明；不连接数据库，不输出环境变量或业务内容。
docker-compose exec -T api python - <<'PYCODE'
import json
from pathlib import Path
from models.agent import Agent,AgentScope,AgentStatus,APP_BACKED_AGENT_SOURCES
print(json.dumps({'check':'agent_model','columns_present':all(x in Agent.__table__.columns for x in ('id','app_id','tenant_id','scope','source','status')),'roster':str(AgentScope.ROSTER),'active':str(AgentStatus.ACTIVE),'app_backed_sources':sorted(str(x) for x in APP_BACKED_AGENT_SOURCES)}))
p=Path('/app/api/controllers/console/__init__.py')
lines=p.read_text().splitlines()
i=next((n for n,x in enumerate(lines) if 'Blueprint(' in x),None)
print(json.dumps({'check':'console_blueprint','declaration':lines[i:i+7] if i is not None else 'NOT_FOUND'}))
PYCODE
