# Dify 3.9.x 性能诊断命令

## 当前：对比 blocking vs streaming 模式吞吐量

```bash
# 测试 blocking 模式（走进程内执行，不经过 Celery/Redis pubsub）
# 用 wrk 或 ab 压测，记录吞吐量

# 测试 streaming 模式（当前模式，经过 Celery + Redis pubsub）
# 同样压测，对比两者差异
```
