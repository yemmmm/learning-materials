#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 18:10
# Context: 已升级 3.12.1，验证：版本落地 + 容器健康 + 迁移命令不再崩于 WORKSPACE_ALREADY_HAS_OWNER
# Cmds: 3 条

# 1. 确认 api/rbac/worker 镜像已是 3.12.1
docker ps --format '{{.Names}} {{.Image}}' | grep -iE 'api|rbac|worker' | head -6

# 2. 容器状态健康（有无重启/退出）
docker-compose ps --format "table {{.Name}}\t{{.Status}}" 2>&1 | head -20

# 3. 重跑迁移 dry-run（之前崩于 WORKSPACE_ALREADY_HAS_OWNER；现在能完整跑完且输出统计 = 双 owner 问题已解除）
docker-compose exec -T api flask rbac-migrate-member-roles 2>&1 | tail -20
