#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-30 23:17
# Context: 代理根因已证实（407），NO_PROXY 已加 minio 并重启服务。本轮做最终验证：容器状态稳定 + 日志无 S3 报错
# Cmds: 2 条

# 1. 查看容器状态（应均为 Up 且无 Restarting）
docker-compose ps 2>&1 | head -10

# 2. 验证日志：无 Failed to connect to S3 / Last session crashed 则彻底修复
docker-compose logs --tail=40 n8n-main-1 2>&1 | grep -iE 's3|crash|error' | tail -8
