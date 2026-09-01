#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-01 12:00
# Context: sandbox 反复重启，启动时 pip install greenlet 失败但手动安装成功，怀疑启动用 python 与默认 python 不一致
# Cmds: 4 条

# 1. 抓 sandbox 启动日志里 greenlet/pip 的原始报错
docker-compose logs --tail=300 sandbox 2>&1 | grep -iE 'greenlet|pip|error|failed' | tail -30

# 2. 容器内实际有哪些 python/pip 及版本（若容器在重启中执行失败，跳过，看第4条）
docker-compose exec -T sandbox sh -c 'which -a python3 pip pip3; python3 -V; pip -V' 2>&1 | head -15

# 3. 容器内 config.yaml 中生效的 python/pip/proxy 配置
docker-compose exec -T sandbox sh -c 'grep -iE "python|pip|proxy" /conf/config.yaml' 2>&1 | head -20

# 4. sandbox 容器退出码与重启次数（exec 失败时的替代信息源）
docker inspect --format '{{.Name}} exit={{.State.ExitCode}} restarts={{.RestartCount}}' $(docker-compose ps -q sandbox) 2>&1 | head -5
