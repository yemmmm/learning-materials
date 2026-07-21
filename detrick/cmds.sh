#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 19:30
# Context: 命令2 traces 入库曲线显示 03:13-03:16 高峰（800-1142条/分钟）后回落，03:24-03:29 空白，03:30-03:41 缓慢尾巴——这就是"压测后缓慢增长"现象。本地验证发现 **analytics_traces 是按小时聚合的物化视图（字段 project_id+hour+countTraces）**，前端查它会有小时级延迟！本轮重点：算端到端延迟（timestamp 业务时间 vs created_at 入库时间）+ 看具体延迟样本 + 查 analytics_traces 物化视图数据 + 确认 ingestion job 状态。
# Cmds: 4 条

# 1. traces 表端到端延迟分布（timestamp 是 Dify 业务时间，created_at 是入库时间；差值就是真正滞后；本地语法已验证 OK）
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT if(dateDiff('second', timestamp, created_at) < 60, 'a_<1min', if(dateDiff('second', timestamp, created_at) < 600, 'b_1-10min', if(dateDiff('second', timestamp, created_at) < 3600, 'c_10-60min', 'd_>60min'))) AS delay_bucket, count() AS traces, max(dateDiff('second', timestamp, created_at)) AS max_delay_sec FROM langfuse.traces WHERE created_at > now() - INTERVAL 6 HOUR GROUP BY delay_bucket ORDER BY delay_bucket FORMAT PrettyCompact" 2>&1 | head -20

# 2. traces 表最近 1 小时延迟最大的 15 个样本（看具体 delay_sec，找端到端滞后直接证据）
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT id, timestamp AS business_time, created_at AS ingest_time, dateDiff('second', timestamp, created_at) AS delay_sec FROM langfuse.traces WHERE created_at > now() - INTERVAL 1 HOUR ORDER BY delay_sec DESC LIMIT 15 FORMAT PrettyCompact" 2>&1 | head -25

# 3. analytics_traces 物化视图数据（前端统计的真实数据源，按小时聚合；对比最近 3 小时 countTraces）
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT project_id, hour, countTraces FROM langfuse.analytics_traces WHERE hour > toStartOfHour(now()) - INTERVAL 3 HOUR ORDER BY hour DESC LIMIT 10 FORMAT PrettyCompact" 2>&1 | head -20

# 4. ingestion-queue / trace-upsert 的 :wait 队列类型（确认是否真的有 waiting 积压，TYPE none = 不存在）
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning TYPE bull:ingestion-queue:wait 2>&1 | head -3
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning TYPE bull:trace-upsert:wait 2>&1 | head -3
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning HMGET bull:ingestion-queue:2914255 name status finishedReason 2>&1 | head -10
