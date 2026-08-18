#!/bin/bash
# === Detrick Troubleshoot Round 16 ===
# Time: 2026-08-19 00:20
# Context: api_websocket 零连接记录，但 /socket.io curl 返回 200——怀疑 200 来自
#          web 前端容器（Next.js 任意路径返回 200 HTML），即 socket.io 实际被路由错了。
#          本轮目标：验证响应体是否为 engine.io 握手包 + 核对 Caddyfile 站点结构。
# Cmds: 2 条 + F12 一项

# 1. 看 socket.io 响应体（0{"sid":...} = 路由正确到 api_websocket；<html/<!DOCTYPE = 路由到 web 前端，实锤）
curl -sk 'https://lp19dksfai18vm.bmwgroup.net/socket.io/?EIO=4&transport=polling' 2>&1 | head -c 200; echo

# 2. Caddyfile 站点与路由结构（看 @socketio 在哪个站点块内、你们访问的域名命中哪个站点）
docker-compose exec -T dify-gateway sh -c 'grep -nE "^[^ #/].*\{|@socketio|reverse_proxy http" /app/gateway_configs/Caddyfile' 2>&1 | head -40

# ===== F12（Network 里点开一个 /socket.io 请求）=====
# 看 Response 体：是 0{"sid":...} 还是 HTML？这一眼定案
