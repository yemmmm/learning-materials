#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 17:00
# Context: 用户工作区角色是 admin，但 account_role_ids 里的角色 d36c6ac4 不含 app_view_layout 权限。本轮目标：查出 d36c6ac4 的角色名和权限内容，定性是角色映射 bug 还是配置问题
# Cmds: 3 条

# 1. 带 inner key 调角色 API（鉴权头猜 X-Inner-Token，401 就试下一条）
docker-compose exec -T api curl -s -H "X-Inner-Token: difyai123456" "http://dify-enterprise-rbac:8086/inner/api/rbac/roles?results_per_page=100" | head -c 2000

# 2. 鉴权头换 Authorization Bearer 再试（哪条返回 JSON 用哪条）
docker-compose exec -T api curl -s -H "Authorization: Bearer difyai123456" "http://dify-enterprise-rbac:8086/inner/api/rbac/roles?results_per_page=100" | head -c 2000

# 3. 在外部数据库的 dify_enterprise 库（rbac 用的库）执行：列出角色相关表名
select table_name from information_schema.tables where table_name like '%role%' or table_name like '%rbac%';
