#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 18:30
# Context: 上轮定位根因！Redis 积压：bull:trace-upsert:events stream 有 10076 entries，bull:ingestion-queue:failed 有 340 members。压测时 trace 涌入速度 > worker 消费速度 → 积压；压测后 worker 慢慢消费，前端 tracing 数持续增长 1-2 小时。应用层配置已确认在 Dify 的 trace_app_config 表（tracing_config json + tracing_provider），与滞后无关。本轮重点：确认积压规模 + worker 资源使用（是否 CPU/内存打满）+ 失败队列内容（340 个失败原因）+ worker 真实处理日志，为解决方案铺路。
# Cmds: 4 条

# 1. 各 Redis 队列积压规模（已知 stream 长度 + 扫描所有 events stream + failed 队列，确认整体积压）
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning XLEN bull:trace-upsert:events 2>&1
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning ZCARD bull:ingestion-queue:failed 2>&1
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning --scan --pattern 'bull:*events' 2>&1 | head -15

# 2. langfuse worker 容器资源使用 + 进程数（CPU/内存是否打满限制消费速度；worker 并发度）
docker stats --no-stream --format "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>&1 | grep -iE 'langfuse' | head -10
docker exec langfuse-langfuse-worker-1 sh -c 'ps -e 2>/dev/null | wc -l; echo "---env concurrency---"; env 2>/dev/null | grep -iE "CONCURRENCY|WORKER|PROCESS|BATCH" | head -10' 2>&1 | head -15

# 3. 失败队列内容（看 340 个失败任务的错误信息，找为什么失败拖慢消费）
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning ZRANGE bull:ingestion-queue:failed 0 1 WITHSCORES 2>&1 | head -20

# 4. langfuse-worker 最近日志（过滤掉无关的 Blob/Mixpanel/PostHog 集成任务，看真正的 trace 消费日志、ClickHouse 写入、重试）
docker logs --tail=500 --since 10m langfuse-langfuse-worker-1 2>&1 | grep -ivE 'Blob Storage|Mixpanel|PostHog|Integration Job|No.*integrations|checkUpdate' | tail -30
