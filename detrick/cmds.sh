#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-31 11:01
# Context: 上轮确认 worker 容器 healthy 且 Redis 配置一致，但看到的是 task runner 日志而非 worker 主进程。本轮看 worker 主进程日志 + Redis 队列里 job 是否积压
# Cmds: 4 条

# 1. worker 主进程最近日志（有没有成功启动、有没有在等 job / 报错）
docker logs --tail 40 n8n-worker-1 2>&1 | tail -40

# 2. worker 日志里过滤执行/任务/错误关键字
docker logs --tail 500 n8n-worker-1 2>&1 | grep -iE 'execution|job|error|refused' | tail -15

# 3. Redis 里 n8n 的 bull 队列 key 列表（看 job 积压在哪些 key）
docker exec n8n-redis redis-cli -a finagentn8n --no-auth-warning --scan --pattern 'bull*' | head -20

# 4. 等待队列长度（如果上条 key 前缀不是 bull_n8n，请替换后再执行一次）
docker exec n8n-redis redis-cli -a finagentn8n --no-auth-warning llen bull_n8n:jobs:wait
