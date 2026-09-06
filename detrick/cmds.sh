#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 12:05
# Context: Dify EE 3.12 RBAC 拒绝（account is not in the resource whitelist），三步迁移已执行仍复现。本轮查：①拒绝日志完整字段 ②member-roles 迁移实际写入情况
# Cmds: 3 条
# 注：api 容器名如不是 dockerapi，请用 docker-compose ps 确认后替换

# 1. 看最近 RBAC 拒绝日志的完整字段（重点看 account id / scene / matched_role_ids）
docker-compose logs --tail=500 dify-enterprise-rbac 2>&1 | grep 'check-access denied' | tail -10

# 2. 重跑 member-roles 迁移看输出（幂等；若显示 0 待迁移说明绑定已写入，若仍有 pending 说明上次没生效）
docker-compose exec -T dockerapi flask rbac-migrate-member-roles 2>&1 | tail -15

# 3. dataset-permissions 迁移 dry-run（不带 --apply，看是否还有待迁移项）
docker-compose exec -T dockerapi flask rbac-migrate-dataset-permissions 2>&1 | tail -15
