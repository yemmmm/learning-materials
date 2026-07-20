#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 15:30
# Context: 上轮发现 ①Dify 的 Langfuse 配置在应用前端页面，存在数据库（不是环境变量）；②Dify api 容器环境变量里有指向 enterprise-collector 的 endpoint（Dify Enterprise 的 OTel 中转层，需确认与前端 Langfuse 配置的关系）；③Redis 需要密码（redis-cli 无密码被拒绝）；④ClickHouse 表结构齐全（traces/observations/events_core/analytics_*）。本轮重点：定位应用层配置表 + enterprise-collector 角色 + ClickHouse traces 实际入库时间分布（验证滞后证据）+ Langfuse worker 消费状态。
# Cmds: 4 条

# 1. 在 Dify 主数据库找应用层可观测性/Langfuse 配置表（前端配置存在哪张表）
docker exec $(docker ps -q --filter "name=db_postgres" | head -1) psql -U postgres -d dify -c "\dt" 2>&1 | grep -iE 'observable|trace|langfuse|telemetry|monitor|opentelemetry|trace_app' | head -15

# 2. enterprise-collector 角色 + 最近日志（是 Dify Enterprise 的 OTel 中转吗？压测时是否堆积/慢？）
docker ps -a --filter "name=enterprise-collector" --format "{{.Names}}: {{.Status}}" 2>&1 | head -3
docker logs --tail=300 $(docker ps -q --filter "name=enterprise-collector" | head -1) 2>&1 | tail -25

# 3. ClickHouse traces 表最近 2 小时按分钟聚合入库量（找滞后证据：压测结束后是否还在持续入库？入库量曲线是平稳还是尖峰后骤降？）
docker exec $(docker ps -q --filter "name=clickhouse" | head -1) clickhouse-client -q "SELECT toStartOfMinute(created_at) AS minute, count() AS traces FROM traces WHERE created_at > now() - INTERVAL 2 HOUR GROUP BY minute ORDER BY minute DESC LIMIT 30" 2>&1 | head -35

# 4. Langfuse 各容器状态 + worker 容器最近日志（worker 消费速度是否跟不上？ClickHouse 写入是否报错？）
docker ps -a --filter "name=langfuse" --format "{{.Names}}: {{.Status}}" 2>&1 | head -10
docker logs --tail=500 $(docker ps -q --filter "name=langfuse-worker\|langfuse_worker\|langfuse" | head -1) 2>&1 | grep -iE 'error|warn|slow|clickhouse|insert|queue|lag|backlog' | tail -20
