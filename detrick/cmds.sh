#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-31 10:55
# Context: n8n 手动触发只有 "enqueued execution (job xxx)"，worker 无日志任务不执行。本轮广撒网：确认 worker 是否运行、main/worker 是否都是 queue 模式、Redis 配置是否一致、worker 日志有无报错
# Cmds: 4 条

# 1. 看 n8n 相关容器是否都在跑（重点看有没有 worker、状态是否 Restarting/Exited）
docker ps -a --format '{{.Names}} {{.Status}}' | grep -iE 'n8n|redis' | head -15

# 2. 对比 main 和 worker 的执行模式 + Redis 连接配置（EXECUTIONS_MODE/REDIS_HOST/DB/PREFIX 必须一致）
for c in $(docker ps --format {{.Names}} | grep -i n8n); do echo "== $c"; docker exec $c env | grep -iE 'EXECUTIONS_MODE|REDIS|BULL' | head -8; done

# 3. 看 worker 最近日志（有无启动成功/连 Redis 报错）
c=$(docker ps --format {{.Names}} | grep -iE 'worker' | head -1); docker logs --tail 25 $c 2>&1 | tail -25

# 4. 过滤 worker 错误日志
c=$(docker ps --format {{.Names}} | grep -iE 'worker' | head -1); docker logs --tail 300 $c 2>&1 | grep -iE 'error|fatal|refused|timeout' | tail -10
