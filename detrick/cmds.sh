#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 14:30
# Context: 上轮 langfuse-minio 标记 unhealthy 但 docker logs 无错误（正常，healthcheck 失败输出在 docker inspect 里、不在容器主进程 stdout）。其它命令无有效返回说明 Dify 侧 grep 关键词没匹配上，需换关键词。本轮重点：定位 MinIO unhealthy 根因 + 验证它是否就是 Langfuse 同步滞后的元凶。
# Cmds: 4 条

# 1. MinIO 最近 5 次健康检查的退出码和输出（unhealthy 的直接证据：超时/错误码/命令失败）
docker ps --filter "name=minio" --format "{{.Names}}: {{.Status}}" 2>&1 | head -3
docker inspect $(docker ps -q --filter "name=minio") --format '{{range .State.Health.Log}}exit={{.ExitCode}} out={{.Output}}{{"\n"}}{{end}}' 2>&1 | tail -15

# 2. 直接探测 MinIO 健康端点响应时间 + 容器内磁盘空间（区分：endpoint 响应慢 vs 配置错 vs 磁盘满）
docker exec $(docker ps -q --filter "name=minio" | head -1) sh -c 'curl -s -o /dev/null -w "live=%{http_code} time=%{time_total}s\nready=" http://localhost:9000/minio/health/live; curl -s -o /dev/null -w "%{http_code} time=%{time_total}s\n" http://localhost:9000/minio/health/ready; df -h 2>&1 | head -5' 2>&1 | head -20

# 3. Langfuse 所有服务最近 1 小时日志中关于 S3/MinIO 的报错（验证 MinIO unhealthy 是否已影响 trace 写入链路）
docker-compose logs --since 1h 2>&1 | grep -iE 'minio|s3|bucket|blob|storage|object' | grep -iE 'error|fail|timeout|refused|exception|503|500|429' | tail -20

# 4. 验证 Dify 是否真在发 trace（用更宽关键词：OTel/Public ingestion/v1/traces）+ Langfuse 接收端最近 1 小时 POST 请求量
docker-compose logs --tail=2000 api 2>&1 | grep -iE 'otel|/api/public|/v1/traces|ingestion|trace_id|langfuse' | tail -15
echo "=== Langfuse ingestion 请求量 ==="
docker-compose logs --since 1h 2>&1 | grep -ciE 'POST /api/public|/api/public/otel|/api/public/ingestion'
