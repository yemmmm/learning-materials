#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 19:00
# Context: INNER_API_KEY=difyai123456 已确认，上轮失败是请求头名不对。本轮：①用正确头名查角色 API ②SQL 列出 dify_enterprise 库全部业务表（兜底直查角色表）
# Cmds: 3 条

# 1. 用 X-Api-Key 头重试角色 API（Dify 内部调用惯例头名）
docker-compose exec -T api curl -s -H "X-Api-Key: difyai123456" "http://dify-enterprise-rbac:8086/inner/api/rbac/roles?results_per_page=100" | head -c 2000

# 2. 用 X-Inner-Api-Key 头再试（两条哪条返回 JSON 用哪条，401 就跳过）
docker-compose exec -T api curl -s -H "X-Inner-Api-Key: difyai123456" "http://dify-enterprise-rbac:8086/inner/api/rbac/roles?results_per_page=100" | head -c 2000

# 3. 在外部数据库的 dify_enterprise 库执行：列出全部业务表（确认角色表真实表名）
select table_schema, table_name from information_schema.tables where table_schema not in ('pg_catalog','information_schema') order by 1,2 limit 50;
