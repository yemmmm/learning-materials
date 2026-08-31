#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-31 00:05
# Context: 上轮确认 Redis 服务端无告警、无代理劫持；本轮看重连日志原文 + Redis timeout 配置 + 重连频率
# Cmds: 3 条

# 1. 看 api_websocket 重连日志的原始内容（哪句话在刷、什么级别）
docker-compose logs --tail=100 api_websocket 2>&1 | tail -30

# 2. 看 Redis 服务端 timeout/tcp-keepalive/maxclients 实际配置值（空闲踢除不产生日志）
docker-compose exec -T redis redis-cli -a difyai123456 CONFIG GET timeout tcp-keepalive maxclients 2>&1 | head -10

# 3. 统计 api_websocket 最近 1 小时重连日志的条数和分布（判断频率是否空闲期触发）
docker-compose logs --since 60m --timestamps api_websocket 2>&1 | grep -iE 'redis|reconnect|retry' | awk '{print substr($1,1,16)}' | sort | uniq -c | tail -15
