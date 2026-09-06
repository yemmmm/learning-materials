#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 00:10
# Context: 实锤——scope=all 是成员快照，必须走控制台 API 才触发成员枚举任务（inner API 不触发）。本轮：用管理员 token 调控制台 PUT whitelist，然后验证 check-access
# Cmds: 3 条（顺序执行）
# 准备：管理员账号（就是报障那位 admin）登录 Dify 控制台 → F12 开发者工具 → Network → 随便点一个请求 → Request Headers 里复制 Authorization: Bearer 后面的整串 token

# 1. 设置变量（把 <TOKEN> 换成刚复制的 token；N 如果控制台不是 80 端口就改成实际地址如 http://localhost:8080）
N=http://localhost; T='<TOKEN>'; I=60a56261-fd3c-47cc-8f63-ad40adee61cf; echo ok

# 2. 调控制台 API 重新保存 scope=all（这次会触发成员枚举任务，给全员写授权）
curl -s -X PUT -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d '{"scope":"all"}' "$N/console/api/workspaces/current/rbac/apps/$I/whitelist"

# 3. 等异步任务跑完后重测 check-access（返回 allowed:true 即修复成功，页面刷新即可打开）
sleep 20; K='Enterprise-Api-Secret-Key: difyai123456'; U=http://dify-enterprise-rbac:8086/inner/api/rbac; TT=e823b48d-382f-43cb-9574-410948f53315; A=dc81582c-3934-4d8f-b034-9cb7809dce2b; docker-compose exec -T api curl -s -X POST -H "$K" -H "X-Inner-Tenant-Id: $TT" -H "X-Inner-Account-Id: $A" -H "Content-Type: application/json" -d "{\"account_id\":\"$A\",\"tenant_id\":\"$TT\",\"scene\":\"app_view_layout\",\"resource_type\":\"app\",\"resource_id\":\"$I\"}" "$U/check-access"
