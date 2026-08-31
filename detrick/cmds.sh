#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-31 00:30
# Context: 已定位为 socketio 库 listen 循环的瞬时异常被记 ERROR；本轮用探针复现抓出真实异常类型（最终确认）
# Cmds: 2 条

# 1. 用与 socketio manager 相同的方式订阅并 listen 90 秒，抓实际抛出的异常类型
docker-compose exec -T api_websocket python -c "
import redis, time
r = redis.Redis(host='redis',port=6379,password='difyai123456',db=0)
p = r.pubsub(); p.subscribe('test_probe')
t = time.time()
while time.time() - t < 90:
    try:
        for m in p.listen():
            pass
    except Exception as e:
        print('EXC ->', type(e).__name__, str(e)[:120])
        time.sleep(1)
print('done, no exception in 90s' )
" 2>&1 | tail -8

# 2. 顺便看下 gunicorn/gevent 相关配置（gevent 与阻塞读的相互作用）
docker-compose exec -T api_websocket env 2>&1 | grep -iE 'GUNICORN|GEVENT|SERVER_WORKER|SOCKETIO' | head -8
