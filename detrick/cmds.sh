#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-30 22:48
# Context: 修正双等号后仍报 Failed to connect to S3。本轮查三点：容器内环境变量是否真的更新（需重建容器而非 restart）、bucket 是否已创建（MinIO 的 /data 下 bucket 是目录）、报错前的完整上下文日志
# Cmds: 3 条

# 1. 确认容器内当前 S3 变量值（若仍带前导 = 说明改动未生效——需要 docker-compose up -d --force-recreate 而不是 restart）
docker-compose exec -T n8n-main-1 sh -c 'env | grep N8N_EXTERNAL_STORAGE | cat -A' 2>&1 | head -10

# 2. 查看 MinIO 数据目录下的 bucket 列表（目录名即 bucket 名，确认 n8n-binary-data 是否存在）
docker-compose exec -T minio sh -c 'ls -la /data 2>/dev/null | head -15' 2>&1 | tail -12

# 3. 查报错前的完整上下文，看有没有被截断的底层错误（如 NoSuchBucket / 403 / DNS）
docker-compose logs --tail=200 n8n-main-1 2>&1 | grep -B5 -A15 'Failed to connect' | head -40
