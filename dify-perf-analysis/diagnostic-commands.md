# Dify 3.9.x 性能诊断命令

## 当前步骤：确认 gunicorn worker 实际数量和配置

```bash
# 1. 查看实际 gunicorn worker 进程数（含 master）
ps aux | grep gunicorn | grep -v grep | wc -l

# 2. 查看完整 gunicorn 启动命令和参数
ps aux | grep gunicorn | grep -v grep | head -3

# 3. 查看 Redis 连接池限制
grep -E 'REDIS_MAX_CONNECTIONS|SERVER_WORKER|GUNICORN' .env | sort -u
```

**目的**：
- 验证 `SERVER_WORKER_AMOUNT` 是否真的产生了 31 个 worker
- 确认 `SERVER_WORKER_CONNECTIONS=500` 是否传递到 gunicorn
- 检查 `REDIS_MAX_CONNECTIONS` 是否构成连接池瓶颈

### 分析公式

当前观察到：`Throughput = Workers / AvgLatency = 31 / 0.387s ≈ 80 req/s`

这说明每个 worker 的并发度 = 1（串行处理请求）。

### 已验证的事实

- `gunicorn 25.1.0` + `--worker-class gevent` → `patch_all()` 被调用 ✓
- `GeventDidPatchBuiltinModulesEvent` 事件触发 ✓
- gRPC 和 psycopg2 被额外 patch ✓
- `queue` 模块可以被正确 patch（即使预导入） ✓
