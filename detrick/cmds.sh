#!/bin/bash
# === Detrick Troubleshoot Round 13 ===
# Time: 2026-07-21
# 本地决定性发现 (commit 上一轮验证):
#   analytics_traces 是普通 View (非物化视图), 且 WHERE 条件为
#     toStartOfHour(timestamp) <= toStartOfHour(subtractHours(now(),1))
#   => 故意排除"当前小时"和"上一小时", 只统计 2 小时前已封闭的小时桶
#   => 这就是前端统计滞后 1-2 小时的根本原因 (不是数据延迟, 是视图设计)
# 本轮在远端 langfuse 库验证此结论: 看视图定义 + 边界值 + 原始分布 vs 统计分布对比
# Cmds: 4 条

# 1. 远端 analytics_traces 视图定义 (重点看 WHERE 条件最后一行)
docker exec langfuse-clickhouse-1 clickhouse-client --query "SHOW CREATE TABLE langfuse.analytics_traces FORMAT Vertical" 2>&1 | head -40

# 2. 边界值: now() 当前小时 vs analytics 截断点 (直观看到 cutoff 卡在2小时前)
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT now() AS current_time, toStartOfHour(now()) AS current_hour, toStartOfHour(subtractHours(now(),1)) AS analytics_cutoff FORMAT Vertical" 2>&1 | head -10

# 3. 原始 traces 每小时分布(近6h) —— 当前小时 + 上一小时都应有大量数据(因为压测数据已实时入库)
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT toStartOfHour(timestamp) AS h, count() AS raw_traces FROM langfuse.traces WHERE timestamp > now() - INTERVAL 6 HOUR GROUP BY h ORDER BY h DESC FORMAT PrettyCompact" 2>&1 | head -15

# 4. analytics_traces 统计的小时分布(近6h) —— 预计只到 2 小时前, 当前/上一小时为空(被WHERE过滤)
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT hour, countTraces FROM langfuse.analytics_traces WHERE hour > now() - INTERVAL 6 HOUR ORDER BY hour DESC FORMAT PrettyCompact" 2>&1 | head -15
