#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-30 23:14
# Context: 用户终端会截断长命令，SDK 测试方案放弃。改用 wget 强制走代理访问 minio（模拟 n8n 走代理访问 S3），若 FAIL 即证明代理是根因
# Cmds: 2 条

# 1. 强制让 wget 走 122.200.106.5:8080 代理访问 minio（FAIL = 代理无法访问 docker 域名 minio，即 S3 报错根因）
docker-compose exec -T n8n-main-1 sh -c 'http_proxy=http://122.200.106.5:8080 wget -q -T 5 -O /dev/null http://minio:9000/minio/health/live && echo VIA-PROXY-OK || echo VIA-PROXY-FAIL' 2>&1 | tail -2

# 2. 查看当前 NO_PROXY 是否已包含 minio（确认修复是否已生效）
docker-compose exec -T n8n-main-1 env 2>&1 | grep -i no_proxy | head -3
