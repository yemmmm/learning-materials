#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 14:26
# Context: 新建 Agent 后他人访问被拒。判别是"成员绑定又空了(bug)"还是"Agent 默认访问范围=特定成员(设计)"。
# 用法：下次复现时【先跑这两条，再跑迁移命令】，把输出带回
# Cmds: 2 条

# 1. 看拒绝日志的 scene 和 reason（若 reason 仍是 not in the resource whitelist，看 scene 是 agent 专属还是通用 app scene）
docker-compose logs --tail=100 dify-enterprise-rbac 2>&1 | grep 'check-access denied' | tail -10

# 2. 关键判别：dry-run 看是否有待迁移成员（0 pending = 绑定没问题，拒绝来自 Agent 默认访问范围，属设计行为，去应用的企业访问控制里改范围即可；有 pending = 又是绑定 bug）
docker-compose exec -T api flask rbac-migrate-member-roles 2>&1 | tail -20
