# Dify 3.9.x 性能诊断命令

## 当前步骤：验证 gunicorn worker 进程数和配置一致性

```bash
# 1. 查看 .env 中 SERVER_WORKER_AMOUNT
grep 'SERVER_WORKER_AMOUNT' .env

# 2. 查看 gunicorn 进程树（父子关系）
ps -eo pid,ppid,user,args --forest | grep gunicorn | grep -v grep
```

**目的**：
- 确认 `--workers 11` 和实际 36 个进程之间的差异来源
- 排除是否有多个 gunicorn 实例或僵尸进程

### 已知数据汇总

| 指标 | 值 |
|------|-----|
| gunicorn 命令 | `--workers 11 --worker-class gevent --worker-connections 500 --timeout 360` |
| ps 进程数 | 36 (含 master) |
| SERVER_WORKER_CONNECTIONS | 500 |
| REDIS_MAX_CONNECTIONS | 未设置 (无限制) |
| gunicorn 版本 | 25.1.0 |
| gevent 版本 | 25.9.1 |
| redis-py 版本 | 7.3.0 |
| patch_all() 调用 | ✓ (GeventDidPatchBuiltinModulesEvent 触发) |
| gRPC/psycopg2 额外 patch | ✓ |

### 公式分析（有待验证）

如果 worker 数为 35：35 / 0.387s = 90 req/s ≈ 80 req/s → 每 worker 并发 ≈ 1
如果 worker 数为 11：11 / 0.387s = 28 req/s ≠ 80 req/s → 每 worker 并发 ≈ 7

**两种情况下，gevent greenlet 并发都远低于理论最大值 500。**
