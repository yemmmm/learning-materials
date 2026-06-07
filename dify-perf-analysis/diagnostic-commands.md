# Dify 3.9.x 性能诊断命令

## 当前：追踪 RedisChannel 命令通道和 Worker 消费逻辑

```bash
docker compose exec api bash -c "grep -rn 'workflow:.*:commands\|command_channel\|RedisChannel' /app/api/core/workflow/ /app/api/core/app/apps/ 2>/dev/null | head -15"
```
