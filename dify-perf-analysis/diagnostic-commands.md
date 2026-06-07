# Dify 3.9.x 性能诊断命令

## 当前：查看 WorkflowAppGenerator.generate() 方法实现

```bash
docker compose exec api bash -c "grep -A 80 'def generate' /app/api/core/app/apps/workflow/app_generator.py 2>/dev/null | head -120"
```
