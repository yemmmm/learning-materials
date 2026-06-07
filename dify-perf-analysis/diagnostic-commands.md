# Dify 3.9.x 性能诊断命令

## 当前步骤：检查 Celery Worker 并发配置（瓶颈假设）

**关键洞察**：`SERVER_WORKER_AMOUNT` 的变化不影响 streaming 吞吐量 → 瓶颈不在 API gunicorn worker，而在 Celery worker。

### streaming 模式执行链路
```
API (gevent) → Celery.delay() → Worker 执行 workflow → Redis pubsub publish → API 订阅接收 → SSE 推送
```

如果 Celery worker 池是瓶颈，增加 API worker 无济于事。

### 计算验证
- Celery worker 执行时间 ~130ms
- 假设 N 个 Celery worker：Max TPS = N / 0.130s
- 如果 N=10：10/0.130 = 77 req/s ≈ 80 req/s ✓

```bash
# 1. Celery worker 相关配置
grep -E 'CELERY_WORKER_AMOUNT|CELERY_AUTO_SCALE|CELERY_WORKER_CONCURRENCY|CELERY_MAX_WORKERS|CELERY_MIN_WORKERS' .env

# 2. Celery worker 实际进程数和启动命令
ps aux | grep celery | grep -v grep | head -10

# 3. worker 容器日志中的并发配置
docker compose logs worker 2>&1 | grep -i "concurrency\|autoscale\|pool\|worker\|ready" | tail -20
```

### Celery worker 并发参数优先级
1. `CELERY_WORKER_CONCURRENCY` — 直接设置并发数（最高优先级）
2. `CELERY_AUTO_SCALE=true` → `--autoscale=${MAX},${MIN}` (MAX 默认 = nproc=20)
3. `CELERY_WORKER_AMOUNT` — 固定并发数（默认 1）
