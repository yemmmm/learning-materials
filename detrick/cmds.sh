#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-31 00:10
# Context: Redis timeout=0 仍持续"连接失败1s重连"；怀疑刷日志的连接与协同用的连接不同，查具体连的是哪个 host + 错误原文
# Cmds: 3 条

# 1. 看日志原文（不过滤），确认报错的具体 host:port 和错误类型
docker-compose logs --tail=20 --timestamps api_websocket 2>&1 | tail -25

# 2. 看 Redis 主机与 event bus 的完整配置（上轮疑似缺 REDIS_HOST）
docker-compose exec -T api_websocket env 2>&1 | grep -iE 'REDIS_HOST|EVENT_BUS|CELERY|LOG_LEVEL' | head -12

# 3. 从容器内直连 Redis 验证（走和业务完全相同的路径）
docker-compose exec -T api_websocket python -c "import redis; r=redis.Redis(host='redis',port=6379,password='difyai123456',db=0,socket_timeout=3); print('PING ->', r.ping())" 2>&1 | tail -5
