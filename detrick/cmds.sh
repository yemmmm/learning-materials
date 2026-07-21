#!/bin/bash
# === Detrick Troubleshoot Round 14 ===
# Time: 2026-07-21
# 用户质疑(正确): 纯视图过滤最多让数据晚1小时(下个整点全显示), 解释不了"压测后持续2小时增长"。
# 命令1(上轮)只证明"已入库数据实时", 不证明"所有数据都已入库"。
# traces 表 3 个时间字段确认: timestamp=业务时间(无DEFAULT,原始), created_at=入库时刻(DEFAULT now()), event_ts=MV版本
# 引擎 ReplacingMergeTree(event_ts) = 异步后台合并去重
# 本轮核心: 验证【数据是否真的延迟入库】—— 看 created_at 入库曲线长尾巴 + 业务时间跨度 + 队列全积压点
# 区分两种可能: (A)数据实时入库,延迟纯视图过滤 / (B)数据延迟入库,压测后还在慢慢灌进ClickHouse
# Cmds: 4 条

# 1. [决定性] created_at 入库曲线(近6h, 10分钟桶) + 每段最大入库延迟
#    解读: 若压测时段后曲线持续高位(长尾巴)+max_lag_sec很大 → 数据延迟入库(场景B坐实)
#          若压测结束曲线立刻归零、max_lag_sec都小 → 数据实时(场景A,纯视图过滤)
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT toStartOfInterval(created_at, INTERVAL 10 MINUTE) AS ingest_bucket, count() AS ingested, max(dateDiff('second', timestamp, created_at)) AS max_lag_sec FROM langfuse.traces WHERE created_at > now() - INTERVAL 6 HOUR GROUP BY ingest_bucket ORDER BY ingest_bucket DESC FORMAT PrettyCompact" 2>&1 | head -40

# 2. 最近30分钟入库的数据, 其业务时间(timestamp)跨度 —— 验证 timestamp 真实性 + 是否延迟补录
#    解读: 若 biz_span_sec 很大(几小时) → 这批数据是延迟补录的(timestamp保留原始时间,数据确实滞后入库)
#          若 biz_span_sec 很小 → 数据实时, timestamp≈created_at
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT min(timestamp) AS min_biz_time, max(timestamp) AS max_biz_time, min(created_at) AS min_ingest, max(created_at) AS max_ingest, count() AS cnt, dateDiff('second', min(timestamp), max(timestamp)) AS biz_span_sec FROM langfuse.traces WHERE created_at > now() - INTERVAL 30 MINUTE FORMAT Vertical" 2>&1 | head -15

# 3. 按业务时间(timestamp)分桶看入库延迟(近6h, 10分钟桶) —— 找出哪些业务时段的数据是延迟入库的
#    解读: 若压测时段(业务时间)的 max_lag_sec 很大(几千秒) → 那批数据是压测后很久才入库的
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT toStartOfInterval(timestamp, INTERVAL 10 MINUTE) AS biz_bucket, count() AS traces, max(dateDiff('second', timestamp, created_at)) AS max_lag_sec FROM langfuse.traces WHERE timestamp > now() - INTERVAL 6 HOUR GROUP BY biz_bucket ORDER BY biz_bucket DESC FORMAT PrettyCompact" 2>&1 | head -40

# 4. ingestion 链路队列全状态(不只看 :wait, 还有 active/delayed/completed) —— 找积压点
#    之前只查了 :wait=none, 本轮看全状态; :delayed 有数据=限流/重试延迟, :active 持续高=处理卡住
for q in ingestion-queue trace-upsert; do
  echo "=== $q ==="
  echo -n "  wait(list): "; docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning LLEN bull:$q:wait 2>&1 | tail -1
  echo -n "  active(zset): "; docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning ZCARD bull:$q:active 2>&1 | tail -1
  echo -n "  delayed(zset): "; docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning ZCARD bull:$q:delayed 2>&1 | tail -1
  echo -n "  completed(zset): "; docker exec langfuse-redis-1 redis-cli -a myredissecret --no-auth-warning ZCARD bull:$q:completed 2>&1 | tail -1
done
