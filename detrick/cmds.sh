#!/bin/bash
# === Detrick Troubleshoot Round 17（修复轮：工作流同步）===
# Time: 2026-08-19 00:55
# Context: 定案——Caddyfile 第 76 行 @socketio 上游是 http://api:5001，
#          应为 http://api_websocket:5001（官方模板默认值）。
#          连接全打到主 api，协作事件不通 → 画布永远"同步数据中"。
# Cmds: 3 条（1 查来源，2 修复，3 验证）

# 1. 查网关的 SOCKETIO 上游变量来源（确认它是被 .env/compose 设成了 api:5001）
docker-compose exec -T dify-gateway sh -c 'printenv | grep -iE "SOCKETIO|UPSTREAM"' 2>&1 | head -5
grep -rn "SOCKETIO" /global/dockerdata/dify-enterprise-3.12.0/.env /global/dockerdata/dify-enterprise-3.12.0/docker-compose.yaml 2>/dev/null | head -5

# 2. 修复：把变量改为 api_websocket:5001 后重建网关容器（按你们实际的配置位置改，
#    优先改 .env 或 compose 里 dify-gateway 服务的 environment，然后执行）：
#    在 .env 中设置/修改：GATEWAY_SOCKETIO_UPSTREAM=api_websocket:5001
docker-compose up -d dify-gateway

# 3. 验证（网关重启后）：
#    a) 确认渲染结果已变
docker-compose exec -T dify-gateway sh -c 'grep -A2 "@socketio" /app/gateway_configs/Caddyfile' 2>&1 | head -4
#    b) 浏览器强刷（Ctrl+Shift+R）重新打开工作流画布，看"同步数据中"是否结束
#    c) 画布打开后立刻看 api_websocket 应出现连接活动
docker-compose logs --tail=15 api_websocket 2>&1 | tail -6
