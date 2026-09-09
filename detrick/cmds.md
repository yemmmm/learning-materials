# 查询 RBAC 角色相关表结构

日期：2026-09-09

用途：为展示指定用户在指定工作空间的角色，确认 RBAC 的成员角色绑定表与角色定义表。此查询只读取表结构，不读取用户数据、不修改数据库。

在 **RBAC 服务实际连接的 PostgreSQL 数据库**中执行以下 SQL，最多返回 30 行。结果用于确认真实表名和字段，随后编写角色关联查询；这不是最终的用户角色查询。

```sql
SELECT
    table_schema,
    table_name,
    string_agg(column_name, ', ' ORDER BY ordinal_position) AS columns
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
GROUP BY table_schema, table_name
HAVING bool_or(
    column_name IN ('role_id', 'role_tag', 'account_id', 'member_id')
)
ORDER BY table_schema, table_name
LIMIT 30;
```

请回传表结构查询结果；无需提供密码、Token 或用户数据。
