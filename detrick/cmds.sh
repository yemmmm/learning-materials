#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 18:01
# Context: scene=app_view_layout 白名单拒绝 + 迁移命令崩于 WORKSPACE_ALREADY_HAS_OWNER（疑似某 workspace 双 owner）。本轮拿完整拒绝行(matched_role_ids 判别) + 定位双 owner 的 workspace
# Cmds: 2 条

# 1. 完整拒绝日志行（关键看 matched_role_ids 字段：空=绑定bug；非空=Agent默认访问范围设计行为）
docker-compose logs --tail=200 dify-enterprise-rbac 2>&1 | grep 'check-access denied' | tail -3

# 2. 查 DB 里 owner 数 >1 的 workspace（定位双 owner 现场在哪）
docker-compose exec -T db psql -U postgres -d dify -c "select tenant_id,count(*) from tenant_members where role='owner' group by 1 having count(*)>1"
