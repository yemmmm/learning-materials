#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-30 22:23
# Context: n8n 企业版启用 S3 二进制存储（指向本机 MinIO）后启动报 Failed to connect to S3，先确认容器内实际生效的 S3 环境变量和到 MinIO 的网络连通性
# Cmds: 3 条

# 1. 查看 main 容器内实际生效的 S3/二进制存储相关环境变量（确认变量名和 endpoint 填的什么）
docker-compose exec -T main env 2>&1 | grep -iE 'S3|BINARY|STORAGE|MINIO' | head -20

# 2. 从 compose 配置里看 S3/MinIO 相关配置（确认 yaml 里写的内容）
docker-compose config 2>&1 | grep -iE 's3|binary|storage|minio' | head -30

# 3. 从 main 容器内分别测试 localhost:9000 和 minio:9000 的连通性（busybox wget，输出 OK 或 FAIL）
docker-compose exec -T main sh -c 'wget -q -T 5 -O /dev/null http://localhost:9000/minio/health/live && echo "localhost:9000 OK" || echo "localhost:9000 FAIL"; wget -q -T 5 -O /dev/null http://minio:9000/minio/health/live && echo "minio:9000 OK" || echo "minio:9000 FAIL"' 2>&1 | tail -5
