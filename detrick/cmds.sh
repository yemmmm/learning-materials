#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 15:20
# Context: RBAC 拒绝场景中 account_role_ids 非空（d36c6ac4）但 matched_role_ids 为空，怀疑用户角色本身不含 app_view_layout 权限。本轮查：①用户工作区角色 ②d36c6ac4 角色名 ③迁移是否覆盖报障租户
# Cmds: 3 条

# 1. 查报障用户在各工作区的角色（重点看 tenant e823b48d 下是 owner/admin/normal/editor）
docker-compose exec -T db psql -U postgres -d dify -c "select tenant_id,role from tenant_members where account_id='dc81582c-3934-4d8f-b034-9cb7809dce2b'" 2>&1 | head -10

# 2. 查 rbac 角色列表，找 d36c6ac4 对应的角色名（看它的权限范围）
docker-compose exec -T api curl -s 'http://dify-enterprise-rbac:8086/inner/api/rbac/roles?page_number=1&results_per_page=100' 2>&1 | head -c 2000

# 3. 确认迁移是否遍历到了报障租户 e823b48d
docker-compose exec -T api flask rbac-migrate-member-roles 2>&1 | grep -E 'tenant=' | tail -10
