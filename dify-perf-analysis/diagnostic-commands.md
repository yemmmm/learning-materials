# Dify 3.9.x 性能诊断命令

## 当前步骤：确认 Celery worker 队列消费者数量

**关键矛盾**：Celery `-P gevent -c 20` 理论最大 154 req/s，但实际仅 80 req/s。

```
理论: 20 greenlets / 0.130s = 154 req/s
实际: 10.4 greenlets / 0.130s = 80 req/s   ← 只有约一半 greenlet 在工作
```

可能原因：
1. workflow_based_app_execution 队列被其他类型的任务抢占了 greenlet
2. 多个 worker 实例分散了并发，但只有部分消费 workflow 队列
3. Celery broker (Redis) 调度延迟导致 greenlet 空闲等待

```bash
# 1. worker 容器内的 celery 进程和完整命令
docker compose exec worker bash -c "ps aux | grep celery | grep -v grep"

# 2. 宿主机所有 celery/worker 进程
ps aux | grep -E "celery|worker" | grep -v grep | grep -v gunicorn

# 3. workflow_based_app_execution 队列的消费者
docker compose logs worker 2>&1 | grep -i "workflow_based_app_execution\|queues" | tail -10

# 4. 检查是否有多个 worker 服务实例
docker compose ps | grep worker
```

### Celery 配置汇总

| 参数 | 值 |
|------|-----|
| Pool | gevent |
| Concurrency | 20 |
| Prefetch Multiplier | 1 |
| Max Tasks Per Child | 50 |
| CELERY_WORKER_AMOUNT | 20 |
| CELERY_AUTO_SCALE | false |
