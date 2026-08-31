#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-31 11:05
# Context: worker-1 日志出现 "Editor is now accessible"/"Instance registered"（main 特征），怀疑 worker 容器实际以 main 角色运行导致队列无人消费；队列前缀确认为 bull:jobs
# Cmds: 3 条

# 1. 四个 n8n 进程的启动命令（worker 必须是 "n8n worker"，如果是 "n8n start"/空 就是根因）
docker inspect --format '{{.Name}} cmd={{.Config.Cmd}}' n8n-worker-1 n8n-worker-2 n8n-main-1 n8n-main-2

# 2. 等待队列积压长度（>0 说明没有 worker 在消费）
docker exec n8n-redis redis-cli -a finagentn8n --no-auth-warning llen bull:jobs:wait

# 3. 活跃/暂停队列长度（job 被取走但卡死会堆在 active）
docker exec n8n-redis redis-cli -a finagentn8n --no-auth-warning llen bull:jobs:active
