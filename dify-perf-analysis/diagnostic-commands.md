# Dify 3.9.x 性能诊断命令

## 当前步骤：决定性实验 — sync vs gevent 模式对比

### 验证过的结论

| 检查项 | 结果 |
|--------|------|
| `patch_all()` 调用 | ✓ (GeventDidPatchBuiltinModulesEvent 触发) |
| gRPC/psycopg2 patch | ✓ |
| Redis pubsub 连接泄漏 | ✗ (正常，80个连接) |
| Celery greenlet 利用率 | ~3% (320槽位，仅用10) |
| API worker 并发 | ~2.4/worker (33 worker，80并发) |

### 瓶颈定位：gevent 在流式路径上并发失效

`--worker-connections 500` 理论上每个 worker 500 greenlet 并发，实际仅 2.4。切换 sync 模式可验证。

### 实验结果：切换到 sync 模式

```bash
# 修改 .env
SERVER_WORKER_CLASS=sync
SERVER_WORKER_AMOUNT=128
# 重启 API
docker compose restart api
# 压测 streaming 模式
```

**判定逻辑**：
- 吞吐量 > 200 req/s → gevent 流式路径有并发缺陷
- 吞吐量 ≈ 80 req/s → 瓶颈在 Celery/Redis 环节
