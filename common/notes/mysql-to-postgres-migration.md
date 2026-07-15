# MySQL → PostgreSQL 数据迁移指南

## 场景

应用层已兼容双数据库，只做数据搬移。作为数据提供方（MySQL），将信息提供给 PG 团队做迁移方案分析。

数据量约十几 GB，可停机迁移。

---

## 需要提供给 PG 团队的信息

### 1. DDL（表结构）

```bash
mysqldump -h <host> -u <user> -p \
  --no-data \
  --routines \
  --triggers \
  --events \
  <db_name> > schema_dump.sql
```

### 2. 数据量概况

```sql
-- 每张表行数和大小
SELECT
    table_name,
    table_rows,
    ROUND(data_length/1024/1024, 2) AS data_mb,
    ROUND(index_length/1024/1024, 2) AS index_mb
FROM information_schema.tables WHERE table_schema = '<db>'
ORDER BY data_length DESC;

-- 库总大小
SELECT table_schema,
    ROUND(SUM(data_length+index_length)/1024/1024, 2) AS total_mb
FROM information_schema.tables GROUP BY table_schema;
```

### 3. 特殊类型与字符集

```sql
-- 字符集
SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = '<db>';

-- ENUM / SET / TINYINT(1) / unsigned 等风险类型
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, DATA_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = '<db>'
  AND (DATA_TYPE IN ('enum','set','tinyint','year')
       OR COLUMN_TYPE LIKE '%unsigned%');
```

### 4. 外键依赖

```sql
SELECT TABLE_NAME, COLUMN_NAME,
       REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = '<db>' AND REFERENCED_TABLE_NAME IS NOT NULL;
```

### 5. 访问信息

| 信息 | 用途 |
|------|------|
| MySQL host:port | 建立连接 |
| 只读账号 + 密码 | pgloader 或导出 |
| 数据库名 | 确认迁移范围 |
| 网络可达性 | 决定直连还是中转 |

### 6. 业务约束

- 停机窗口多长
- 表名/字段名是否需要调整
- PG 账号/权限要求
- MySQL 是否保留（回滚策略）

---

## 迁移流程

| 步骤 | 操作 |
|------|------|
| 全量迁移 | `pgloader` 一键搞定 |
| 增量同步 | 停服跳过，不停服用 CDC/双写 |
| 序列修正 | `SELECT setval('table_id_seq', COALESCE((SELECT max(id) FROM table), 1))` |
| 数据校验 | 行数 + checksum + 抽样对比 |
| 切流 | MySQL 只读 → 追平 → 切 PG |

---

## 注意事项

- 全量导入后建索引和外键，速度更快
- 注意 JSON 字段、TEXT/BLOB、空值/重复数据等特殊场景
- PG 连接数更敏感，建议配合 PgBouncer
- 迁移后 MySQL 保留一段时间作为回滚后手
