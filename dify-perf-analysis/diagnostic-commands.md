# Dify 3.9.x 性能诊断命令

## 当前步骤：诊断 Redis 连接泄漏 (~29000 connections)

**关键发现**：Redis connections 29000 且持续增长 → 连接泄漏

### Redis 连接分析

```bash
# 1. 压测前连接基线
echo "=== 压测前 ==="
docker compose exec redis redis-cli CLIENT LIST | wc -l

# 2. 压测中连接类型分布
docker compose exec redis redis-cli CLIENT LIST | awk '{print $3}' | sort | uniq -c | sort -rn | head -10

# 3. 统计 pubsub 连接数
docker compose exec redis redis-cli CLIENT LIST | grep -c "sub=1"

# 4. Redis 客户端列表（看连接存活时间）
docker compose exec redis redis-cli CLIENT LIST | awk '{print $2, $12}' | head -20
```

### 已知数据汇总 (压测期间)

| 指标 | 值 | 分析 |
|------|-----|------|
| API TCP 连接 (/proc/net/tcp) | 406→700+→400 | 300+ 额外连接正常 |
| API 副本数 | 3 (`--scale api=3`) | 每副本 11 worker |
| API CPU | ~40% | 非 CPU 瓶颈 |
| Redis connections | ~29000 持续增长 | 连接泄漏! |
| Redis blocked | 16 | 正常（Celery BRPOP） |
| Celery workers | 16 实例 × 20 greenlets | 320 并发槽位 |

### 诊断逻辑

- 正常情况: pubsub 连接 = 并发请求数 ≈ 100-300
- 如果 pubsub 连接远大于此 → pubsub 连接未正确释放
- 检查 `stream_topic_events()` 的 `with topic.subscribe()` 是否正确清理
