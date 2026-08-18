#!/bin/bash
# === Detrick Troubleshoot Round 12（验证轮）===
# Time: 2026-08-18 21:50
# Context: 三步迁移已成功执行（migrated=1）。本文件在 UI 复测后使用：
#          重新登录 console → 试改访问权限/开工作流页 → 再执行下面命令看拒绝是否消失。
# Cmds: 2 条

# 1. 复测操作后，看 rbac 最近是否还有 check-access denied（应无新增；有则看 scene 是什么）
docker-compose logs --tail=200 dify-enterprise-rbac 2>&1 | grep -E 'check-access denied|"severity":"(WARN|ERROR)"' | tail -5

# 2. 确认你的账号当前的 RBAC 角色绑定状态（members/rbac-roles 查询，status 200 即接口正常）
docker-compose logs --tail=200 dify-enterprise-rbac 2>&1 | grep '78e64483' | tail -5
