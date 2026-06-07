# Dify 3.9.x 性能诊断命令

## 当前：追踪 .delay() 调用后的结果返回逻辑

```bash
docker compose exec api bash -c "grep -A 30 'execute_workflow_professional.delay\|execute_workflow_team.delay\|execute_workflow_sandbox.delay' /app/api/services/async_workflow_service.py 2>/dev/null | head -80"
```
