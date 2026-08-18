#!/bin/bash
# === Detrick Troubleshoot Round 19（WS 握手后立即断连，定位断点）===
# Time: 2026-08-19 09:15
# Context: 网关已重启，浏览器 socket.io 走 websocket 但状态 finished
#          （= 连接建立后立刻断开，客户端反复重连）。
#          需要区分：路由仍是旧上游？还是 api_websocket 接了但主动断开？
# Cmds: 3 条

# 1. 运行容器内实际渲染的 Caddyfile 上游 + 网关最近日志（找 websocket/错误字样）
docker-compose exec -T dify-gateway sh -c 'grep -A2 "@socketio" /app/gateway_configs/Caddyfile' 2>&1 | head -4
docker-compose logs --tail=40 dify-gateway 2>&1 | grep -iE 'socket|websocket|error|proxy' | tail -10

# 2. 画布打开状态下看 api_websocket 有无任何连接痕迹（哪怕断连也会有日志），
#    并从 api 容器内部直连 api_websocket 验证服务本身健康
docker-compose logs --since 10m api_websocket 2>&1 | tail -8
docker-compose exec -T api sh -c 'curl -s -m 5 "http://api_websocket:5001/socket.io/?EIO=4&transport=polling"' 2>&1 | head -c 200; echo

# 3. F12 → Network → 点开那条 finished 的 socket.io websocket 请求 →
#    切到 "Messages"（帧）标签页：
#    a) 有没有帧内容？贴出最后 2-3 条（含 "40" / "0" 开头的数字帧）
#    b) 帧是绿色(发出)还是红色(错误/断开标记)？
echo "==> 执行 1/2 后回贴输出；第 3 条在浏览器观察帧内容"
