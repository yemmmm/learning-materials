#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 17:30
# Context: 上轮关键突破！CLICKHOUSE_URL=http://default:langfuse@clickhouse:8123/langfuse，最后 /langfuse 是数据库名！**trace 数据写在 langfuse 数据库，不是 default**——之前所有 ClickHouse 查询都查错了库，所以只看到 schema_migrations。命令1 确认 LANGFUSE_INGESTION_* 参数未设置（用默认值），不是滞后参数问题。命令3 web 日志只有 checkUpdate 错误（封闭网络正常），无 trace 接收错误。命令4 dify/enterprise 库无 observable/trace 表，应用层配置在别处。本轮重点：验证 ClickHouse langfuse 库是否存在 + trace 数据实际写入情况 + langfuse-worker 消费日志 + Dify 应用层配置存储列。
# Cmds: 4 条

# 1. 列出 ClickHouse 所有数据库（直接验证 langfuse 库是否真的存在；本地验证查询语法 OK）
docker exec langfuse-clickhouse-1 clickhouse-client --query "SHOW DATABASES" 2>&1 | head -10

# 2. 查 langfuse 库的所有非空表行数+大小（**核心**：验证 trace 是否真的写入了；如果 langfuse 库不存在或全空，证明 trace 从未入库）
docker exec langfuse-clickhouse-1 clickhouse-client --query "SELECT name, total_rows, formatReadableSize(total_bytes) AS size FROM system.tables WHERE database='langfuse' AND total_rows > 0 ORDER BY total_rows DESC LIMIT 25 FORMAT PrettyCompact" 2>&1 | head -35

# 3. langfuse-langfuse-worker-1 容器最近 30 分钟日志（worker 是消费 Redis 队列写 ClickHouse 的核心，看它有没有报错/慢/堆积）
docker logs --tail=300 --since 30m langfuse-langfuse-worker-1 2>&1 | tail -30

# 4. 在 Dify 数据库中搜索含 trace/langfuse/tracing 字段的表和列（找应用层 Langfuse 配置存储位置，可能在 app 或 app_model_config 表的 JSON 字段里）
docker exec $(docker ps -q --filter "name=db_postgres" | head -1) psql -U postgres -d dify -c "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='public' AND (column_name LIKE '%trace%' OR column_name LIKE '%langfuse%' OR column_name LIKE '%tracing%' OR column_name LIKE '%observable%' OR column_name LIKE '%telemetry%') ORDER BY table_name LIMIT 30" 2>&1 | head -35
