#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-30 22:53
# Context: 上轮 3 条命令结果未回传（粘贴被截断）。S3 仍连不上，新增怀疑：容器内全局代理变量劫持了到 MinIO 的请求（环境存在企业 TLS 拦截）。本轮 4 条 = 上轮 3 条 + 代理检查
# Cmds: 4 条

# 1. 【新增】检查容器内是否设置了全局代理（若 HTTP_PROXY/HTTPS_PROXY 存在，S3 请求可能被劫持去走代理导致连不上 MinIO）
docker-compose exec -T n8n-main-1 sh -c 'env | grep -iE "proxy|no_proxy" | cat -A' 2>&1 | head -10

# 2. 确认容器内当前 S3 变量值是否已更新（若仍带前导 = 说明需要 --force-recreate 重建容器）
docker-compose exec -T n8n-main-1 sh -c 'env | grep N8N_EXTERNAL_STORAGE | cat -A' 2>&1 | head -10

# 3. 查看 MinIO 数据目录下的 bucket 列表（目录名即 bucket 名，确认 n8n-binary-data 是否已创建）
docker-compose exec -T minio sh -c 'ls -la /data 2>/dev/null | head -15' 2>&1 | tail -12

# 4. 查 S3 报错前后的完整上下文日志（找底层错误码，如 NoSuchBucket / 403 / ECONNREFUSED）
docker-compose logs --tail=200 n8n-main-1 2>&1 | grep -B5 -A15 'Failed to connect' | head -40
