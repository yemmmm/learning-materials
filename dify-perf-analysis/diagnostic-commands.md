# Dify 3.9.x 性能诊断命令

## 当前：追踪 .delay() 调用后的结果返回逻辑

```bash
docker compose exec api bash -c "grep -B 10 -A 40 'workflow_based_app_execution_task.delay' /app/api/services/app_generate_service.py 2>/dev/null | head -100"
```
