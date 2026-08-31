#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-31 11:08
# Context: worker 命令正确但 bull:jobs:wait 积压 6 个 job 无人消费，worker 日志有反复 Lost Redis connection；另 n8n-main-2 容器不存在。本轮验证 worker 启动状态与 Redis 连接稳定性
# Cmds: 4 条

# 1. worker 启动关键日志（有没有 "Worker started"/并发数/就绪字样）
docker logs n8n-worker-1 2>&1 | grep -iE 'worker|started|concurrency|ready' | head -12

# 2. worker 累计 Redis 断连次数（数字大 = 连接极不稳定，接近根因）
docker logs n8n-worker-1 2>&1 | grep -c 'Lost Redis'

# 3. Redis 当前客户端连接数与限制（connected_clients vs maxclients）
docker exec n8n-redis redis-cli -a finagentn8n --no-auth-warning info clients | head -4

# 4. 现在手动触发一次工作流，等 1 分钟后执行本条，看 worker 最近 5 分钟有无反应
docker logs --since 5m n8n-worker-1 2>&1 | tail -30
