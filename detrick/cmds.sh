#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 18:00
# Context: 上轮重大突破！ClickHouse 有 langfuse 数据库，trace 数据正常写入（traces 166万行、observations 253万行、blob_storage_file_log 401万行）。worker 日志只有定时集成任务无错误。**所以"滞后"是真的，需直接验证**。traces 表有 event_ts（事件时间）和 created_at（入库时间），差值就是真实延迟。本轮重点：查 traces 最近 3 小时入库分布 + 算延迟分布 + Redis 队列状态 + Dify 应用层配置（外部 PostgreSQL，用户提供 SQL 自己执行）。
# Cmds: 4 条（前3条在 langfuse 服务器执行；第4条是 SQL，用户在 Dify 外部 PostgreSQL 执行）

# 1. langfuse.traces 最近 3 小时按分钟入库量（找滞后证据：压测结束后是否还在持续批量入库？曲线是平还是尖峰？）
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT toStartOfMinute(created_at) AS minute, count() AS traces FROM langfuse.traces WHERE created_at > now() - INTERVAL 3 HOUR GROUP BY minute ORDER BY minute DESC LIMIT 60 FORMAT PrettyCompact" 2>&1 | head -65

# 2. traces 表入库延迟分布（created_at - event_ts；如果 >60min 的 trace 占比高，就直接证明"1-2 小时滞后"现象）
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT if(dateDiff('second', event_ts, created_at) < 60, 'a_<1min', if(dateDiff('second', event_ts, created_at) < 600, 'b_1-10min', if(dateDiff('second', event_ts, created_at) < 3600, 'c_10-60min', 'd_>60min'))) AS delay_bucket, count() AS traces, max(dateDiff('second', event_ts, created_at)) AS max_delay_sec FROM langfuse.traces WHERE created_at > now() - INTERVAL 6 HOUR GROUP BY delay_bucket ORDER BY delay_bucket FORMAT PrettyCompact" 2>&1 | head -20

# 3. Redis 队列状态（密码从上轮 env 拿到 myredissecret；DBSIZE 大说明有积压；bigkeys 看哪个队列积压最多）
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning DBSIZE 2>&1 | head -3
docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning --bigkeys 2>&1 | tail -30

# 4. 【请在 Dify 外部 PostgreSQL 执行下面打印的 SQL】查找应用层 Langfuse 配置存储位置
cat <<'SQL'
-- ===== 在 Dify 外部 PostgreSQL 执行以下 SQL =====
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema='public'
  AND (column_name LIKE '%trace%'
       OR column_name LIKE '%langfuse%'
       OR column_name LIKE '%tracing%'
       OR column_name LIKE '%observable%'
       OR column_name LIKE '%telemetry%')
ORDER BY table_name, column_name
LIMIT 50;
SQL
