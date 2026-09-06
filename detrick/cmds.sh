#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 22:30
# Context: app 60a56261 的 whitelist 已设为 scope=all，但页面仍报无权限。本轮绕过页面直接调 rbac check-access，判定是缓存问题还是判定条件问题
# Cmds: 3 条（顺序执行，1 必须先跑）

# 1. 设置变量（同一终端内后续命令依赖）
K='Enterprise-Api-Secret-Key: difyai123456'; U=http://dify-enterprise-rbac:8086/inner/api/rbac; T=e823b48d-382f-43cb-9574-410948f53315; A=dc81582c-3934-4d8f-b034-9cb7809dce2b; I=60a56261-fd3c-47cc-8f63-ad40adee61cf; echo ok

# 2. 直接调 check-access（复现页面的判定请求，看 allowed 是 true 还是 false）
docker-compose exec -T api curl -s -X POST -H "$K" -H "X-Inner-Tenant-Id: $T" -H "X-Inner-Account-Id: $A" -H "Content-Type: application/json" -d "{\"account_id\":\"$A\",\"tenant_id\":\"$T\",\"scene\":\"app_view_layout\",\"resource_type\":\"app\",\"resource_id\":\"$I\"}" "$U/check-access"

# 3. 看 PUT 之后页面尝试的最新拒绝日志（reason 是否变化）
docker-compose logs --since 30m dify-enterprise-rbac 2>&1 | grep 'check-access denied' | tail -5
