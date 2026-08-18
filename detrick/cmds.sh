#!/bin/bash
# === Detrick Troubleshoot Round 13 ===
# Time: 2026-08-18 22:40
# Context: 迁移后角色管理恢复 ✅。剩余两个独立问题：
#          A. 所有人（含 owner）卡工作流同步 → 疑似 Caddy 缺 /socket.io 路由（WebSocket）
#          B. 非 owner 仍不能改 webapp 访问权限 → 看最新拒绝原因（白名单 or 角色权限项）
# Cmds: 4 条（A 三条 + B 一条）

# A1. 浏览器 WebSocket 握手是否被网关正确路由（直接探测 socket.io 端点；
#     返回 200=路由正常，404/502=路由缺失实锤。若网关容器名不同请替换）
curl -sk -o /dev/null -w 'socket.io HTTP %{http_code}\n' 'https://lp19dksfai18vm.bmwgroup.net/socket.io/?EIO=4&transport=polling'

# A2. 网关容器内 Caddyfile 的 socket.io / websocket 相关路由（服务名可能是 dify-gateway）
docker-compose exec -T dify-gateway sh -c 'grep -rn "socket.io" /app/gateway_configs/ /etc/caddy/ 2>/dev/null' 2>&1 | head -10

# A3. api_websocket 服务日志（有没有收到过 socket.io 连接、有无报错）
docker-compose logs --tail=200 api_websocket 2>&1 | grep -iE 'socket|error|fail|connect' | tail -10

# B1. 角色分配后，rbac 最新的 check-access denied 原因（还是 resource whitelist 吗？scene 是什么？）
docker-compose logs --tail=300 dify-enterprise-rbac 2>&1 | grep 'check-access denied' | tail -3
