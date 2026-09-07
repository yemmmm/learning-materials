#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 09:50
# Context: 昨日 RBAC 迁移已修复旧 workspace 401；今日用户新加入另一 workspace 后进入工作流仍报白名单 401，怀疑新成员加入路径未写入角色绑定
# Cmds: 3 条

# 1. 看 RBAC 服务最近的拒绝日志（拿 scene/reason/tenant_id，确认是否仍是 whitelist 拒绝）
docker-compose logs --tail=300 dify-enterprise-rbac 2>&1 | grep 'check-access denied' | tail -15

# 2. member-roles 迁移 dry-run（默认不落库；若显示新 workspace 成员待迁移，即坐实"新加入成员无绑定"）
docker-compose exec -T api flask rbac-migrate-member-roles 2>&1 | tail -20

# 3. 确认当前 api/rbac 镜像版本（3.12.0 还是 3.12.1，后者修了多个 RBAC bug）
docker ps --format '{{.Names}} {{.Image}}' | grep -iE 'api|rbac' | head -5
