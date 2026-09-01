#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-01 14:30
# Context: 已定位根因：容器为 python3.14，requirements.txt 钉死 greenlet==3.1.1 无 cp314 whl 导致源码编译失败；本轮执行修复并验证
# Cmds: 4 条

# 1. 修复前先确认挂载卷里 requirements.txt 第6行的钉死版本
grep -n greenlet volumes/sandbox/conf/requirements.txt

# 2. 把 greenlet==3.1.1 改为 3.5.5（已验证 3.14 下可装的版本）并回显确认
sed -i 's/greenlet==3.1.1/greenlet==3.5.5/' volumes/sandbox/conf/requirements.txt && grep -n greenlet volumes/sandbox/conf/requirements.txt

# 3. 顺便确认启动用 python 与默认 python 是否同一个（收尾验证之前的猜想）
docker-compose exec -T sandbox sh -c 'which -a python3 pip; pip -V' 2>&1 | head -10

# 4. 重启 sandbox 并等 40 秒看启动日志是否装依赖成功（不再 panic）
docker-compose up -d sandbox && sleep 40 && docker-compose logs --tail=30 sandbox 2>&1 | tail -25
