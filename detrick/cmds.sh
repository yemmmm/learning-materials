#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 03:20
# Context: SSO-only 登录拿不到控制台 token。改为直接复刻枚举任务：调 inner API PUT /apps/user-access-policies 给全员绑 default 策略（与源码 initialize_created_app_rbac_access_task 完全等价）
# Cmds: 3 条（顺序执行）

# 1. 在外部数据库执行，拿到全部成员的 account_id 列表：
select account_id from tenant_account_joins where tenant_id='e823b48d-382f-43cb-9574-410948f53315';

# 2. 把成员 id 填进 account_ids 数组（["id1","id2",...]），执行绑定（operator 用 A 即可）
K='Enterprise-Api-Secret-Key: difyai123456'; U=http://dify-enterprise-rbac:8086/inner/api/rbac; TT=e823b48d-382f-43cb-9574-410948f53315; A=dc81582c-3934-4d8f-b034-9cb7809dce2b; I=60a56261-fd3c-47cc-8f63-ad40adee61cf; docker-compose exec -T api curl -s -X PUT -H "$K" -H "X-Inner-Tenant-Id: $TT" -H "X-Inner-Account-Id: $A" -H "Content-Type: application/json" -d "{\"access_policy_ids\":[\"default\"],\"account_ids\":[\"ID1\",\"ID2\"]}" "$U/apps/user-access-policies?app_id=$I"

# 3. 重测 check-access（allowed:true 即修复成功）
docker-compose exec -T api curl -s -X POST -H "$K" -H "X-Inner-Tenant-Id: $TT" -H "X-Inner-Account-Id: $A" -H "Content-Type: application/json" -d "{\"account_id\":\"$A\",\"tenant_id\":\"$TT\",\"scene\":\"app_view_layout\",\"resource_type\":\"app\",\"resource_id\":\"$I\"}" "$U/check-access"
