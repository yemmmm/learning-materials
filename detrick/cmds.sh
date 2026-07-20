#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 15:00
# Context: 上轮两个关键发现 ①MinIO unhealthy 是 healthcheck 用了 curl 但镜像无 curl 导致的假性告警（磁盘 44%、无 S3 报错、可忽略）；②之前在 langfuse 目录下执行 docker-compose 命令查的是 Langfuse 自己的服务（api/worker/minio），没查到 Dify 容器——所以"Dify 无 Langfuse 日志"是查错地方。本轮重点：用 docker 原生命令绕过目录限制，定位 Dify→Langfuse 对接方式 + 检查 Langfuse 内部消费链路。
# Cmds: 4 条

# 1. 列出所有运行中 docker 容器（定位 Dify api 容器名 + Langfuse web/worker/clickhouse/redis 各自容器名）
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" 2>&1 | head -40

# 2. 进 Dify api 容器查 Langfuse/OTel 环境变量（确认对接方式：OTel HTTP Exporter？应用内 SDK？batch 间隔？endpoint 是否正确？）
docker exec $(docker ps -q --filter "name=api" | head -1) env 2>&1 | grep -iE 'langfuse|otel|otlp|trace|exporter|telemetry' | head -25

# 3. Langfuse 各容器状态（web/worker/clickhouse/redis/db）+ 最近 30 分钟日志中 worker/clickhouse/queue 相关报错（找消费滞后证据）
docker ps -a --filter "name=langfuse" --format "{{.Names}}: {{.Status}}" 2>&1 | head -10
docker-compose logs --since 30m 2>&1 | grep -iE 'worker|clickhouse|queue|lag|delay|backlog|redis' | grep -iE 'error|warn|slow|timeout|refused|process' | tail -15

# 4. 直接看 Redis 队列堆积情况 + ClickHouse 表清单（Redis DBSIZE 异常大说明 worker 消费跟不上；ClickHouse 是 Langfuse v3 的实际存储后端）
docker exec $(docker ps -q --filter "name=redis" | head -1) redis-cli DBSIZE 2>&1 | head -3
docker exec $(docker ps -q --filter "name=clickhouse" | head -1) clickhouse-client -q "SHOW TABLES" 2>&1 | head -15
