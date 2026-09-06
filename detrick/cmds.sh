#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 01:00
# Context: 浏览器里找不到 Authorization token，改用登录 API 直接换 access_token，然后调控制台 whitelist API 触发成员枚举
# Cmds: 3 条（顺序执行）

# 1. 设置变量（换成 admin 的邮箱和密码；控制台端口不是 80 就改 N）
N=http://localhost; E='admin@example.com'; P='password-here'; I=60a56261-fd3c-47cc-8f63-ad40adee61cf; echo ok

# 2. 登录换 token（从返回 JSON 里复制 data.access_token 的值，一长串 JWT）
curl -s -X POST -H "Content-Type: application/json" -d "{\"email\":\"$E\",\"password\":\"$P\",\"remember_me\":true}" "$N/console/api/login" | head -c 600

# 3. 把 <TOKEN> 换成刚拿到的 access_token 后执行（触发全员授权枚举）
T='<TOKEN>'; curl -s -X PUT -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d '{"scope":"all"}' "$N/console/api/workspaces/current/rbac/apps/$I/whitelist"
