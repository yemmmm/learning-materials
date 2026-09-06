#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 23:20
# Context: whitelist 已是 scope=all 但 check-access 仍 allowed:false，怀疑 rbac Go 服务存在判定缓存。本轮：重启 rbac 清缓存后直接重测
# Cmds: 3 条（顺序执行）

# 1. 重设变量并重启 rbac 容器（清掉内存中的判定/白名单缓存，约 10 秒）
K='Enterprise-Api-Secret-Key: difyai123456'; U=http://dify-enterprise-rbac:8086/inner/api/rbac; T=e823b48d-382f-43cb-9574-410948f53315; A=dc81582c-3934-4d8f-b034-9cb7809dce2b; I=60a56261-fd3c-47cc-8f63-ad40adee61cf; docker-compose restart dify-enterprise-rbac

# 2. 等 rbac 起来后重测 check-access（如果这次 true，就是缓存问题，页面直接恢复）
sleep 15; docker-compose exec -T api curl -s -X POST -H "$K" -H "X-Inner-Tenant-Id: $T" -H "X-Inner-Account-Id: $A" -H "Content-Type: application/json" -d "{\"account_id\":\"$A\",\"tenant_id\":\"$T\",\"scene\":\"app_view_layout\",\"resource_type\":\"app\",\"resource_id\":\"$I\"}" "$U/check-access"

# 3. 对照实验：找一个升级后新建的、你能正常打开的工作流 app id（浏览器地址栏 /app/<id>/workflow 里的 id），替换 NEWID 后执行，看正常场景的 check-access 返回结构
docker-compose exec -T api curl -s -X POST -H "$K" -H "X-Inner-Tenant-Id: $T" -H "X-Inner-Account-Id: $A" -H "Content-Type: application/json" -d "{\"account_id\":\"$A\",\"tenant_id\":\"$T\",\"scene\":\"app_view_layout\",\"resource_type\":\"app\",\"resource_id\":\"NEWID\"}" "$U/check-access"
