#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 04:10
# Context: 成员 100+ 无法手填。改为在 api 容器内直接同步执行官方枚举任务 initialize_created_app_rbac_access_task（自动读全员、逐批绑定 default 策略），先对 60a56261 单点执行
# Cmds: 2 条（顺序执行）

# 1. 对报障 app 同步执行官方枚举任务（成功会输出 task-done，成员多时可能跑十几秒）
docker-compose exec -T api python -c "from app_factory import create_app; wsgi, app = create_app(); app.app_context().push(); from tasks.initialize_created_app_rbac_access_task import initialize_created_app_rbac_access_task as t; t.apply(args=('e823b48d-382f-43cb-9574-410948f53315','dc81582c-3934-4d8f-b034-9cb7809dce2b','60a56261-fd3c-47cc-8f63-ad40adee61cf')); print('task-done')"

# 2. 重测 check-access（allowed:true 即修复成功，页面刷新即可打开）
K='Enterprise-Api-Secret-Key: difyai123456'; U=http://dify-enterprise-rbac:8086/inner/api/rbac; TT=e823b48d-382f-43cb-9574-410948f53315; A=dc81582c-3934-4d8f-b034-9cb7809dce2b; docker-compose exec -T api curl -s -X POST -H "$K" -H "X-Inner-Tenant-Id: $TT" -H "X-Inner-Account-Id: $A" -H "Content-Type: application/json" -d "{\"account_id\":\"$A\",\"tenant_id\":\"$TT\",\"scene\":\"app_view_layout\",\"resource_type\":\"app\",\"resource_id\":\"60a56261-fd3c-47cc-8f63-ad40adee61cf\"}" "$U/check-access"
