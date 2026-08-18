#!/bin/bash
# === Detrick Troubleshoot Round 14 ===
# Time: 2026-08-18 23:10
# Context: rbac denied 已消失（角色迁移生效）。剩余：
#          A. 全员卡工作流同步 → 验证 /socket.io WebSocket 路由（最关键，3 条）
#          B. 非 owner 改访问权限仍失败 → 需重新抓取当前失败请求（F12）
# Cmds: 3 条

# A1. 探测 socket.io 端点（200=路由正常；404/502/000=Caddy 缺 /socket.io 路由实锤）
curl -sk -o /dev/null -w 'socket.io HTTP %{http_code}\n' 'https://lp19dksfai18vm.bmwgroup.net/socket.io/?EIO=4&transport=polling'

# A2. 网关 Caddyfile 中 socket.io 路由段（无输出=缺失；服务名可能叫 dify-gateway，不同请替换）
docker-compose exec -T dify-gateway sh -c 'grep -rn "socket.io" /app/gateway_configs/ /etc/caddy/ 2>/dev/null' 2>&1 | head -10

# A3. api_websocket 最近日志（有无 socket.io 连接进入、有无报错）
docker-compose logs --tail=200 api_websocket 2>&1 | tail -8

# ===== B. F12 重新抓取（非 owner 账号操作"修改访问权限"失败时）=====
# 贴出失败请求的：URL、方法、状态码、响应 body
# （rbac 已无拒绝记录，需确认现在失败在哪一层：可能不再是 401）
