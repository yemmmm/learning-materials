#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-31 00:20
# Context: 连接正常但 receive 循环刷 ERROR；直接看容器内 redis_manager.py:188 的触发条件 + 订阅是否存活
# Cmds: 3 条

# 1. 挖出企业版 redis_manager.py 第 160-200 行源码（看 188 行报错的触发条件）
docker-compose exec -T api_websocket sh -c 'f=$(find /app -name redis_manager.py 2>/dev/null | head -1); echo $f; sed -n "160,200p" $f' 2>&1 | head -50

# 2. 看 Redis 当前活跃的 Pub/Sub 订阅通道（确认协同订阅还活着）
docker-compose exec -T redis redis-cli -a difyai123456 PUBSUB CHANNELS 2>/dev/null | head -10

# 3. 用同样的客户端做 30 秒空闲订阅测试（复现读超时是否抛异常）
docker-compose exec -T api_websocket python -c "
import redis, time
r = redis.Redis(host='redis',port=6379,password='difyai123456',db=0)
p = r.pubsub(); p.subscribe('test_probe')
t=time.time()
try:
    m = p.get_message(timeout=20); print('20s idle get_message ->', m)
except Exception as e: print('EXC ->', type(e).__name__, e)
" 2>&1 | tail -5
