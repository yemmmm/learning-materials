#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 19:00
# Context: 修正上轮判断！worker CPU 仅 2.66%（空闲），日志过滤后无 trace 处理记录，bigkeys 显示 Redis 里 0 个 list（:wait 队列空），340 个 failed 是 5 个月前旧任务。bull:trace-upsert:events（stream）是 BullMQ 事件日志不是积压。**worker 消费慢导致积压的假设被推翻**。新假设：①ClickHouse 批量写入延迟；②前端查 analytics_traces 物化视图（定期刷新）；③前端缓存。本轮重点：对比原始表 vs 聚合视图数据差异 + traces 真实入库曲线 + 真正的 BullMQ 队列状态 + worker 处理频率。
# Cmds: 4 条

# 1. 对比原始表 vs 聚合视图的数据量+最新时间（如果 analytics_traces 落后 traces，证明前端查的是延迟刷新的物化视图）
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT 'traces' AS tbl, count() AS rows, max(created_at) AS latest FROM langfuse.traces UNION ALL SELECT 'analytics_traces', count(), max(created_at) FROM langfuse.analytics_traces UNION ALL SELECT 'observations', count(), max(created_at) FROM langfuse.observations UNION ALL SELECT 'analytics_observations', count(), max(created_at) FROM langfuse.analytics_observations FORMAT PrettyCompact" 2>&1 | head -25

# 2. traces 表最近 2 小时按分钟入库量（精确看曲线：压测高峰 + 停止后是否还有持续入库尾巴）
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT toStartOfMinute(created_at) AS minute, count() AS traces FROM langfuse.traces WHERE created_at > now() - INTERVAL 2 HOUR GROUP BY minute ORDER BY minute DESC LIMIT 60 FORMAT PrettyCompact" 2>&1 | head -65

# 3. 真正的 BullMQ 队列结构（扫描各队列的子 key：wait/active/completed/failed，确认是否真的空）
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning --scan --pattern 'bull:ingestion-queue:*' 2>&1 | head -15
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning --scan --pattern 'bull:trace-upsert:*' 2>&1 | head -15
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning --scan --pattern 'bull:entity-change-queue:*' 2>&1 | head -15

# 4. worker 最近 10000 行日志中各队列/操作的处理频率（看 worker 真正在处理什么、ClickHouse 写入频率）
docker logs --tail=10000 langfuse-langfuse-worker-1 2>&1 | grep -ioE 'ingestion-queue|trace-upsert|otel-ingestion|score-upsert|observation-upsert|entity-change|clickhouse|insert|batch' | sort | uniq -c | sort -rn | head -15
