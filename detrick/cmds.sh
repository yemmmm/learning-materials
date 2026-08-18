#!/bin/bash
# === Detrick Troubleshoot Round 2 ===
# Time: 2026-08-18 16:05
# Context: 上轮日志显示 Inner* 内部接口全 200（api↔enterprise 及 DB 链路正常），
#          但 console 端 UpdateWebAppWhitelistSubjects 返回 401 ErrUnauthorized
#          "unauthorized to access this resource"。
#          本轮目标：确认 401 是"所有 console 端企业接口都失败"（token 认证问题）
#          还是"个别接口失败"（角色权限问题），并查当前账号在工作区的角色。
# Cmds: 3 条

# 1. 最近 2000 行日志中所有 401 记录按接口统计（看 401 影响范围：全部 console 接口 or 个别）
docker-compose logs --tail=2000 dify-enterprise 2>&1 | grep -E 'status" ?: ?"?401' | sed -E 's/.*api\.enterprise\.([A-Za-z]+)\/([A-Za-z]+).*reason" ?: ?"?([^"]+)".*/\1\/\2 (\3)/' | sort | uniq -c | sort -rn | head -10

# 2. 非 Inner 的 console 端接口成败分布（有没有任何 console 端企业接口返回过 200）
docker-compose logs --tail=2000 dify-enterprise 2>&1 | grep 'api.enterprise.' | grep -v Inner | sed -E 's/.*api\.enterprise\.([A-Za-z]+)\/([A-Za-z]+).*status" ?: ?"?([0-9]+).*/\1\/\2 \3/' | sort | uniq -c | sort -rn | head -10

# 3. 当前账号在工作区的角色（db 服务名不同请替换；role 应为 owner/admin 才能改访问权限）
docker-compose exec -T db psql -U postgres -d dify -c "SELECT a.email, aj.role, aj.status FROM tenant_account_joins aj JOIN accounts a ON a.id = aj.account_id ORDER BY aj.last_active_at DESC NULLS LAST LIMIT 5" 2>&1 | head -12
