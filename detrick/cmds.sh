#!/bin/bash
# === Detrick Troubleshoot Round 20（确认并修复前端 Socket URL）===
# Time: 2026-08-19 10:50
# Context: 网关上游虽已手改为 api_websocket，但全员仍卡“同步数据中”。旧版升级环境可能缺少
#          NEXT_PUBLIC_SOCKET_URL，导致 web 默认发布 ws://localhost；同时用正确变量名固化网关上游。
# Cmds: 3 条

# 1. 取证：查看两个容器当前实际变量，并确认运行中 Caddyfile 的全部 socket.io 上游
docker-compose exec -T web sh -c 'printf "NEXT_PUBLIC_SOCKET_URL="; printenv NEXT_PUBLIC_SOCKET_URL' 2>&1 | head -3
docker-compose exec -T dify-gateway sh -c 'printf "GATEWAY_SOCKET_IO_UPSTREAM="; printenv GATEWAY_SOCKET_IO_UPSTREAM; grep -n -A2 "@socketio path" /app/gateway_configs/Caddyfile' 2>&1 | head -15

# 2. 取证：从容器内按浏览器的真实 HTTPS 域名走完整网关路径；正常应返回 HTTP 200 和以 0{ 开头的 Socket.IO 握手包
docker-compose exec -T api sh -c 'curl -ksS -i -m 8 "https://lp19dksfai18vm.bmwgroup.net/socket.io/?EIO=4&transport=polling&t=round20"' 2>&1 | head -15

# 3. 修复：若变量不是目标值，备份 .env、写入 HTTPS 对应的 wss 地址和正确网关变量名，重建 3 个相关服务并复验
WEB_SOCKET_NOW=$(docker-compose exec -T web sh -c 'printenv NEXT_PUBLIC_SOCKET_URL' 2>/dev/null | tr -d '\r')
GATEWAY_UPSTREAM_NOW=$(docker-compose exec -T dify-gateway sh -c 'printenv GATEWAY_SOCKET_IO_UPSTREAM' 2>/dev/null | tr -d '\r')
if [ "$WEB_SOCKET_NOW" != "wss://lp19dksfai18vm.bmwgroup.net" ] || [ "$GATEWAY_UPSTREAM_NOW" != "api_websocket:5001" ]; then
  BACKUP_FILE=".env.before-round20-$(date +%Y%m%d-%H%M%S)"
  cp -p .env "$BACKUP_FILE"
  for KV in 'NEXT_PUBLIC_SOCKET_URL=wss://lp19dksfai18vm.bmwgroup.net' 'GATEWAY_SOCKET_IO_UPSTREAM=api_websocket:5001'; do
    KEY=${KV%%=*}
    if grep -q "^${KEY}=" .env; then sed -i "s|^${KEY}=.*|${KV}|" .env; else printf '\n%s\n' "$KV" >> .env; fi
  done
  echo "backup=$BACKUP_FILE"
  docker-compose up -d --force-recreate web api_websocket dify-gateway 2>&1 | tail -12
else
  echo "变量已正确，无需重建容器"
fi
docker-compose exec -T web sh -c 'printf "web_socket="; printenv NEXT_PUBLIC_SOCKET_URL' 2>&1 | head -3
docker-compose exec -T dify-gateway sh -c 'printf "gateway_upstream="; printenv GATEWAY_SOCKET_IO_UPSTREAM; grep -A2 "@socketio path" /app/gateway_configs/Caddyfile' 2>&1 | head -8
echo "完成后用 Ctrl+Shift+R 强制刷新画布；回贴以上 3 条输出和 finished 请求的 Request URL。"
