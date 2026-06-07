# Dify 3.9.x 性能诊断命令

## 当前步骤：验证 API gunicorn worker 的实际并发连接数

**关键发现**：16 个 Celery worker × 20 greenlets = 320 并发槽位，但只用了 ~3%（~10 个）→ 瓶颈在上游 API 到 Celery 的环节。

### 架构确认

| 组件 | 实例数 | 并发模型 | 单实例并发 | 总并发槽位 |
|------|--------|----------|-----------|-----------|
| API (gunicorn) | 11 workers | gevent | 500 connections | 5500 |
| Celery | 16 instances | gevent pool | 20 greenlets | 320 |
| Redis | 1 | - | - | - |

**理论瓶颈**: 320 Celery 槽位 → 320/0.130s = 2461 req/s
**实际吞吐量**: 80 req/s → 仅用 ~10 个 Celery 槽位

```bash
# 1. 压测期间，查看 API 容器的 ESTABLISHED 连接数
# 在压测同时运行，观察峰值
docker compose exec api bash -c "ss -tnp | grep :5001 | grep ESTAB | wc -l"

# 2. 压测期间，查看 API 容器 CPU 使用率
docker stats --no-stream | grep api

# 3. 压测期间，查看 Redis 瞬时 OPS
docker compose exec redis redis-cli --stat
# (Ctrl+C 退出)
```

### 诊断逻辑
- 如果连接数 > 100 但吞吐量仍是 80 → gevent greenlet 切换有问题
- 如果连接数 ≈ 80 且 CPU 低 → API worker 被 I/O 阻塞（gevent 未生效的表现）
- 如果连接数 ≈ 80 且 CPU 高 → API worker 达到 CPU 瓶颈
