#!/bin/bash
# === Detrick Troubleshoot Round 10 ===
# Time: 2026-08-18 20:50
# Context: 迁移命令存在；企业服务日志无任何 seed/迁移记录。
#          本轮用 --dry-run 只读预览（不写任何数据）实证"成员角色迁移是否执行过"：
#          有待迁移成员 → 升级迁移缺失实锤；无待迁移 → 排除，定性官方 bug。
# Cmds: 2 条（均只读）

# 1. 预览成员角色迁移（--dry-run 只预览不写入；看输出里有多少成员待迁移、是否包含 admin 账号）
docker-compose exec -T api flask rbac-migrate-member-roles --dry-run 2>&1 | tail -25

# 2. 顺带确认数据集权限迁移命令存在（只看帮助，不执行）
docker-compose exec -T api flask rbac-migrate-dataset-permissions --help 2>&1 | head -12
