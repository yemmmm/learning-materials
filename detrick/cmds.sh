#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 02:30
# Context: 网关是 Caddy 且强制 HTTPS（80→308），登录改走 https + -k。拿到 token 后完成 whitelist 修复并验证
# Cmds: 3 条（顺序执行，同一终端）

# 1. 用 https 登录换 token（E/P 换成 admin 邮箱密码；从返回里复制 data.access_token）
N=https://localhost; E='admin@example.com'; P='password-here'; curl -sk -X POST -H "Content-Type: application/json" -d "{\"email\":\"$E\",\"password\":\"$P\",\"remember_me\":true}" "$N/console/api/login" | head -c 600

# 2. 把 <TOKEN> 换成拿到的 access_token 后执行（触发全员授权枚举）
T='<TOKEN>'; I=60a56261-fd3c-47cc-8f63-ad40adee61cf; curl -sk -X PUT -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d '{"scope":"all"}' "$N/console/api/workspaces/current/rbac/apps/$I/whitelist"

# 3. 等 20 秒后重测 check-access（allowed:true 即修复成功）
sleep 20; K='Enterprise-Api-Secret-Key: difyai123456'; U=http://dify-enterprise-rbac:8086/inner/api/rbac; TT=e823b48d-382f-43cb-9574-410948f53315; A=dc81582c-3934-4d8f-b034-9cb7809dce2b; docker-compose exec -T api curl -s -X POST -H "$K" -H "X-Inner-Tenant-Id: $TT" -H "X-Inner-Account-Id: $A" -H "Content-Type: application/json" -d "{\"account_id\":\"$A\",\"tenant_id\":\"$TT\",\"scene\":\"app_view_layout\",\"resource_type\":\"app\",\"resource_id\":\"$I\"}" "$U/check-access"
