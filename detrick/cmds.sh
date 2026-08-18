#!/bin/bash
# === Detrick Troubleshoot Round 11（修复轮）===
# Time: 2026-08-18 21:20
# Context: 定性完成——升级时未执行官方强制的 RBAC 迁移（dry-run 实锤：2 成员待迁移、0 绑定）。
#          官方文档要求迁移完成前成员（除 owner）无任何权限，与全部症状吻合。
#          ⚠️ 以下命令会写入数据，请安排停机窗口执行，按顺序逐条执行并在每条完成后检查输出。
# Cmds: 3 条修复 + 2 条验证

# 1. 迁移成员角色绑定（从 dry-run 预览过的同款命令去掉 --dry-run）
docker-compose exec -T api flask rbac-migrate-member-roles 2>&1 | tail -10

# 2. 迁移数据集权限/白名单绑定（--apply 真正写入）
docker-compose exec -T api flask rbac-migrate-dataset-permissions --apply 2>&1 | tail -10

# 3. 回填插件自动升级数据
docker-compose exec -T api flask backfill-plugin-auto-upgrade 2>&1 | tail -10

# ===== 验证（迁移完成后，用你的普通账号重新登录 console）=====
# 4. 重新测试：修改 web 应用访问权限是否不再 401；工作流是否不再卡"同步数据中"
# 5. 迁移后仍不能改访问权限 → 属预期权限设计（normal 角色无 app_access_config 权限），
#    让 owner 在成员设置里把你提升为 admin/编辑，或由 owner 操作；
#    角色分配功能此时应已恢复（之前失效也是迁移缺失所致）
