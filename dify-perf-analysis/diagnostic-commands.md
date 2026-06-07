# Dify 3.9.x 性能诊断命令

## 1. 确认 Celery 结果轮询方式

```bash
# 查看 Celery result backend 配置
docker compose exec api bash -c "grep -r 'CELERY_RESULT\|result_backend\|interval\|polling' /app/api/configs/ 2>/dev/null"

# 查看工作流核心代码中的 Celery 调用方式
docker compose exec api bash -c "grep -rn '\.get(\|AsyncResult\|wait(' /app/api/core/workflow/ 2>/dev/null | head -20"
```

> **结果**: core/workflow/ 中没有 AsyncResult，都是普通 dict.get()。Celery 调用在更上层。

### 继续追踪：API 控制器/服务层中的 Celery 调用

```bash
docker compose exec api bash -c "grep -rn 'send_task\|apply_async\|\.delay(' /app/api/controllers/ /app/api/services/ 2>/dev/null | grep -i workflow | head -20"
```

## 2. 测量各阶段耗时

```bash
# 测 blocking 模式端到端耗时
time curl -X POST http://localhost:5001/v1/workflows/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"inputs": {}, "response_mode": "blocking"}'

# 测 streaming 模式耗时对比
time curl -X POST http://localhost:5001/v1/workflows/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"inputs": {}, "response_mode": "streaming"}'
```

## 3. 检查 gevent 兼容性

```bash
docker compose exec api python -c "
import gevent.monkey
print('patch_all called:', hasattr(gevent.monkey, 'saved'))
import redis
print('redis module:', redis.__file__)
from redis.connection import Connection
print('Connection base:', Connection.__bases__)
"
```

## 4. Redis 连接与慢查询

```bash
docker compose exec redis redis-cli -a difyai123456 CLIENT LIST | wc -l

docker compose exec redis redis-cli -a difyai123456 INFO stats

docker compose exec redis redis-cli -a difyai123456 SLOWLOG GET 10
```

## 5. PostgreSQL 连接数

```bash
docker compose exec db_postgres psql -U postgres -d dify -c \
  "SELECT count(*) as active, (SELECT setting::int FROM pg_settings WHERE name='max_connections') as max FROM pg_stat_activity;"
```

## 6. API 进程系统调用分析

```bash
docker compose exec api strace -c -p $(pgrep -f gunicorn | head -1) -T
```

## 7. 渐进式调优测试矩阵

```bash
# 测试 1：基准线
SERVER_WORKER_AMOUNT=31

# 测试 2：sync 公式
SERVER_WORKER_AMOUNT=41

# 测试 3：gevent 精简
SERVER_WORKER_AMOUNT=20

# 固定 Worker 侧参数
CELERY_WORKER_AMOUNT=4
docker compose up -d --scale worker=6
```
