#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-31 00:00
# Context: api_websocket 日志全是重连 Redis，但多人协同正常；确认日志形态与所连 Redis 配置
# Cmds: 3 条

# 1. 看 api_websocket 重连日志的具体内容与频率（错误关键词过滤+时间戳）
docker-compose logs --tail=300 --timestamps api_websocket 2>&1 | grep -iE 'redis|reconnect|error|retry' | tail -30

# 2. 看 api_websocket 实际使用的 Redis 连接配置（HOST/DB/SENTINEL/代理）
docker-compose exec -T api_websocket env 2>&1 | grep -iE 'REDIS|PROXY' | head -15

# 3. 看 Redis 服务端是否有踢客户端/超时/最大连接数类告警
docker-compose logs --tail=200 redis 2>&1 | grep -iE 'timeout|close|maxclients|error|warning' | tail -20
