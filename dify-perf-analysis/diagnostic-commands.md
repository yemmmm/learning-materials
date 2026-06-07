# Dify 3.9.x 性能诊断命令

## 当前步骤：验证 gunicorn worker 是否调用了 patch_all()

通过检查 gunicorn.conf.py 中 `post_patch` 回调的日志输出，确认 monkey-patching 是否生效。

```bash
docker compose logs api 2>&1 | grep -i "patched with gevent\|gRPC patched\|psycopg2 patched"
```

**预期输出**：如果 patching 正常，应看到：
- `gRPC patched with gevent.`
- `psycopg2 patched with gevent.`

**空输出意味着**：`patch_all()` 从未被调用，gevent monkey-patching 完全不生效。

### 上下文

通过本地镜像分析：
- gunicorn 版本 25.1.0，`GeventWorker.patch()` 正确调用了 `monkey.patch_all()`
- `gunicorn.conf.py` 订阅了 `GeventDidPatchBuiltinModulesEvent`，在 patch 完成后会打印确认日志
- `post_patch` 回调还会 patch gRPC 和 psycopg2

如果此命令输出为空，则 gunicorn worker 根本没有执行 monkey-patching，导致：
- 所有 gevent worker 退化为同步阻塞模式
- 每个 worker 同一时间只能处理 1 个请求
- 31 workers × 387ms = 80 req/s（与压测数据精确吻合）
