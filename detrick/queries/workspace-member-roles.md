# 查询用户在工作空间的 RBAC 角色

日期：2026-09-09

状态：已关闭（2026-09-09，用户确认）。本轮定位结束，无需继续执行或回传；以下 SQL 保留供功能开发参考。关闭不代表现场用户数据或功能实现已验收，验证范围见下文。

用途：展示指定用户在指定工作空间的角色。以下 SQL 只读，不修改数据库。

## 本机已确认的结构

2026-09-09，从本机企业版 PostgreSQL 停用数据目录的隔离副本实际查询确认：

- 数据库：`enterprise`，schema：`public`。现场数据库名以 RBAC 连接配置为准。
- `rbac_bindings`：包含 `tenant_id`、`account_id`、`role_id`。
- `rbac_roles`：包含 `id`、`name`、`type`、`category`、`is_builtin`、`permission_keys`、`role_template_id` 等字段。
- 通过 `rbac_bindings.role_id = rbac_roles.id` 关联。
- 本机 `rbac_roles` 没有 `role_tag` 列，不能直接照搬 API 返回字段。
- 本机保留的 RBAC 镜像为 3.12.0。这两张本地表为空；已验证 SQL 能执行，未验证现场用户数据或 3.12.1 结构。

## 查询指定用户的角色

在 RBAC 数据库中执行，将两个占位符替换为真实 UUID。一个用户可能返回多条角色，页面展示各条 `role_name`；`permission_keys` 是每个角色的权限定义，不等于具体资源最终鉴权结果。

```sql
SELECT
    b.tenant_id,
    b.account_id,
    r.id AS role_id,
    r.name AS role_name,
    r.type,
    r.category,
    r.is_builtin,
    r.permission_keys
FROM public.rbac_bindings AS b
JOIN public.rbac_roles AS r ON r.id = b.role_id
WHERE b.tenant_id = '<租户 UUID>'::uuid
  AND b.account_id = '<用户 UUID>'::uuid
ORDER BY r.name, r.id;
```

## 如现场结构不同，再查询表结构

在 **RBAC 服务实际连接的 PostgreSQL 数据库**中执行以下 SQL，最多返回 30 行。结果用于对照现场表名和字段。

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
