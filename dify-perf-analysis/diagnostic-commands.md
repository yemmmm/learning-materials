# Dify 3.9.x 性能诊断命令

## 当前：streaming 模式，找到 WorkflowAppGenerator 类位置

> 上一步发现：streaming 模式下 .delay() 在 on_subscribe 回调中触发。需追踪 WorkflowAppGenerator 实现。

```bash
docker compose exec api bash -c "grep -rn 'class WorkflowAppGenerator' /app/api/ 2>/dev/null"
```
