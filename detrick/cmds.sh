#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 17:00
# Context: 上轮澄清！容器名是 langfuse-langfuse-1（不是 langfuse-web-1）和 langfuse-langfuse-worker-1，**web 和 worker 都已 Up 11 天正常运行**。端口 3000/3001/8123 都在监听。之前命令1、4 无输出是因为过滤器 name=langfuse-web 不匹配（容器名里没有 web 字样）。但 ClickHouse traces/observations/scores 三表为空（max=1970）—— 怀疑德勤 Langfuse v3.183 把数据写到了 events_core/event_log 等其它表（v3 新事件存储模型），或根本没写入。本轮重点：用正确容器名重查 ingestion 参数 + 找 trace 实际存储表（所有非空表）+ web 接收日志 + Dify 应用层 Langfuse 配置。
# Cmds: 4 条

# 1. langfuse-langfuse-1 容器中 ingestion 调优参数（**LANGFUSE_INGESTION_QUEUE_DELAY_MS / WRITE_INTERVAL_MS 被设大就是滞后直接原因**）+ 关键 URL 配置
docker exec langfuse-langfuse-1 env 2>&1 | grep -iE 'INGESTION|QUEUE_DELAY|WRITE_INTERVAL|REDIS_AUTH|CLICKHOUSE_URL|NEXTAUTH_URL|S3_EVENT' | head -20

# 2. ClickHouse 所有非空表的行数+大小（找 trace 实际写到哪张表，v3.183 可能用 events_core 而非 traces；本地已验证查询语法 OK）
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT name, total_rows, formatReadableSize(total_bytes) AS size FROM system.tables WHERE database='default' AND total_rows > 0 ORDER BY total_rows DESC LIMIT 25 FORMAT PrettyCompact" 2>&1 | head -35

# 3. langfuse-langfuse-1（web）容器最近 30 分钟日志（看 trace 接收处理情况、ClickHouse 写入错误、Redis 队列堆积）
docker logs --tail=300 --since 30m langfuse-langfuse-1 2>&1 | tail -30

# 4. Dify 应用层 Langfuse 配置表（前端页面配置存在数据库哪张表，分别查 dify 和 enterprise 库）
docker exec $(docker ps -q --filter "name=db_postgres" | head -1) psql -U postgres -d dify -c "\dt" 2>&1 | grep -iE 'observable|trace|langfuse|telemetry|monitor' | head -15
docker exec $(docker ps -q --filter "name=db_postgres" | head -1) psql -U postgres -d enterprise -c "\dt" 2>&1 | grep -iE 'observable|trace|langfuse|telemetry|monitor' | head -15
