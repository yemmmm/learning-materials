#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 16:00
# Context: 上轮命令3、4 均无输出。本地验证：①traces 表 schema 正常（created_at DateTime64(3)），查询语法 OK（本地表为空只是因为本地 langfuse web/worker 未启动）。②读本地 docker-compose.yml 发现两个**直接控制滞后**的关键参数：LANGFUSE_INGESTION_QUEUE_DELAY_MS（队列读取间隔）和 LANGFUSE_INGESTION_CLICKHOUSE_WRITE_INTERVAL_MS（CH 写入间隔），默认为空（内部默认几百 ms～几秒），**如果被设大就是滞后直接原因**。本轮重点：验证 ingestion 参数 + traces 实际数据量 + 列出 langfuse 完整容器名 + 看 web 接收端日志。
# Cmds: 4 条

# 1. 查 langfuse-web 容器中的 ingestion 调优参数（**LANGFUSE_INGESTION_QUEUE_DELAY_MS / LANGFUSE_INGESTION_CLICKHOUSE_WRITE_INTERVAL_MS 被设大就是滞后直接原因**）+ Redis 密码
docker exec $(docker ps -q --filter "name=langfuse-web" | head -1) env 2>&1 | grep -iE 'INGESTION|QUEUE_DELAY|WRITE_INTERVAL|REDIS_AUTH|NEXTAUTH_URL|SALT|ENCRYPTION_KEY' | head -15

# 2. ClickHouse 三张核心表数据量 + 最新入库时间（验证 worker 是否在持续入库；如果 latest 是几小时前/几天前说明 worker 已停；本地已验证查询语法 OK）
docker exec $(docker ps -q --filter "name=clickhouse" | head -1) clickhouse-client --query "SELECT 'traces' AS tbl, count() AS rows, max(created_at) AS latest FROM traces UNION ALL SELECT 'observations', count(), max(created_at) FROM observations UNION ALL SELECT 'scores', count(), max(created_at) FROM scores FORMAT PrettyCompact" 2>&1 | head -25

# 3. 列出所有 langfuse 相关容器（完整名称+镜像+状态，确认 web/worker 实际名字，不要 head -1 截断）
docker ps -a --filter "name=langfuse" --format "{{.Names}}\t{{.Image}}\t{{.Status}}" 2>&1 | head -20

# 4. langfuse-web 容器最近 30 分钟日志（看 trace 接收处理情况、是否有堆积/慢/错误/批量写入迹象）
docker logs --tail=300 --since 30m $(docker ps -q --filter "name=langfuse-web" | head -1) 2>&1 | tail -30
