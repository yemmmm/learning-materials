#!/bin/bash
# === Detrick Troubleshoot Round 18（验证 socket.io 路由修复为何未生效）===
# Time: 2026-08-19 08:40
# Context: 用户已把 template 中 @socketio 上游改为 api_websocket:5001，
#          但画布仍卡"同步数据中"，api_websocket 无连接日志。
#          本轮验证断点在哪层：渲染结果？Caddy 重载？还是 api_websocket 不可达。
# 注意：如果改的是宿主机 gateway_configs/ 下的文件，先执行
#       docker-compose restart dify-gateway   再跑下面的验证！
# Cmds: 3 条

# 1. 运行中的网关容器里实际渲染出的 Caddyfile 是否已指向 api_websocket，
#    以及网关最近日志有无重载/报错
docker-compose exec -T dify-gateway sh -c 'grep -A2 "@socketio" /app/gateway_configs/Caddyfile' 2>&1 | head -4
docker-compose logs --tail=25 dify-gateway 2>&1 | tail -12

# 2. 确认 api_websocket 容器在跑，且从集群内部能完成 engine.io 握手
#    （用 api 容器当跳板，它自带 curl）
docker-compose ps api_websocket 2>&1 | head -4
docker-compose exec -T api sh -c 'curl -s -m 5 "http://api_websocket:5001/socket.io/?EIO=4&transport=polling"' 2>&1 | head -c 200; echo

# 3. 浏览器侧实况：F12 → Network → 筛选 "socket.io"，刷新画布后观察：
#    a) 请求完整 URL（走的是哪个域名/端口）
#    b) 该请求的 Protocol 列是 "websocket" 还是普通 http（轮询）
#    c) 若是 websocket：状态码是 101 还是一直 pending/失败；
#       若是轮询：请求是否一直挂起不返回
#    把看到的三点描述回来即可（不用截图）
echo "==> 请执行上面 2 条命令，并按第 3 条在浏览器观察后回贴结果"
