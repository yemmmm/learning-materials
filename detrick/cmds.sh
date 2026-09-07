#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 11:27
# Context: 已确认报错是 Dify EE 已知 bug（v3.12.1 修复），最后验证服务器当前 Dify 版本是否 <= 3.12.0，以闭环"升级即可修复"的结论
# Cmds: 2 条
# 注意：在 Dify 的 docker-compose 目录下执行

# 1. 看 api 容器实际使用的镜像 tag（确认版本）
docker ps --format '{{.Names}}\t{{.Image}}' | grep -iE 'api|worker' | head -5

# 2. 容器内 pyproject.toml 的版本号（镜像 tag 可能被本地重打过，以代码内版本为准）
docker-compose exec -T api sh -c 'grep -m1 ^version /app/api/pyproject.toml' 2>&1 | head -3
