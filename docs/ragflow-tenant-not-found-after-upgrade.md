# RAGFlow 升级后 "Tenant not found" 定位文档

## 背景

- **场景**：离线服务器将 RAGFlow 从 0.23.0 升级到 0.25.4
- **数据库**：PostgreSQL（PG 路径迁移代码在 `api/db/db_models.py:1509-1583`）
- **症状**：创建知识库时报错 `error:root:Tenant not found.`
- **次要现象**：日志中伴随大量 `opentelemetry.trace_exporter: failed to export span batch due to timeout`（**与本问题无关，见末尾说明**）

## 根因定位

### 报错代码位置

`api/db/services/knowledgebase_service.py:420-422`：

```python
# Verify tenant exists
ok, _t = TenantService.get_by_id(tenant_id)
if not ok:
    return False, get_data_error_result(message="Tenant not found.")
```

注意：错误字符串带句号 `.`，grep 时有两个候选位置（`mcp_api.py:138`、`knowledgebase_service.py:422`），KB 创建场景下一定是后者。

### 日志机制：为什么看到 `error:root:Tenant not found.`

`api/utils/api_utils.py:120-127` 的 `get_data_error_result` 不仅构造错误响应，**还会主动记录日志**：

```python
def get_data_error_result(code=RetCode.DATA_ERROR, message="Sorry! Data missing!"):
    if sys.exc_info()[0] is not None:
        logging.exception(message)   # 有活跃异常时记完整堆栈
    else:
        logging.error(message)        # 无异常时只记一行
```

`logging.error(message)` 用 root logger 输出的格式就是 `error:root:<message>`，与 `Tenant not found.` 拼起来正好是 `error:root:Tenant not found.`。

**判别两种情况**：

| 日志形态 | 含义 | 走向 |
|---|---|---|
| 只有一行 `error:root:Tenant not found.`，**无堆栈** | `get_by_id()` 走 happy path 但 `get_or_none()` 返回 None → 该 id 的 tenant 行确实查不到 | 数据问题（id 不匹配 / 数据库不对） |
| `error:root:Tenant not found.` 后**跟 Traceback** | `get_by_id()` 内部抛异常被 `except Exception: pass` 吞掉 | schema 问题（列缺失 / 类型不匹配） |

### `get_by_id` 仅按 id 过滤

`api/db/services/common_service.py:288`：

```python
try:
    obj = cls.model.get_or_none(cls.model.id == pid)
    if obj:
        return True, obj
except Exception:
    pass                # 异常被吞了！
return False, None     # → 触发 "Tenant not found"
```

无 status、无其他过滤。但因为 `except Exception: pass` 的存在，**任何 DB 异常都会被伪装成 "Tenant not found"**，这是该函数最大的坑。

### `tenant_id` 来源

`api/utils/api_utils.py:236-244` 的 `add_tenant_id_to_kwargs` 装饰器：

```python
def add_tenant_id_to_kwargs(func):
    @wraps(func)
    async def wrapper(**kwargs):
        from api.apps import current_user
        kwargs["tenant_id"] = current_user.id
        ...
```

`current_user.id` = 当前登录用户的 id。

### RAGFlow 的不变量

注册时 `tenant["id"] = user_id`（`api/db/joint_services/user_account_service.py:65`）：

```python
tenant = {
    "id": user_id,
    ...
}
```

即 **`tenant.id == user.id`**。能登录说明 user 表里这行存在；创建 KB 报 "Tenant not found" 只能说明 **同样 id 的 tenant 行不存在**。

## 升级场景下的可能成因（按概率排序）

### 原因 1：数据库实际未真正迁移（最常见）

- 只换了 RAGFlow 镜像，但新容器连到了不同的 MySQL
- MySQL 数据卷未正确挂载（误用 `docker compose down -v` 删过卷）
- `service_conf.yaml.template` 中 MySQL 地址 / 库名变了
- 备份恢复时只恢复了 `user` 表，没恢复 `tenant` 表

### 原因 2：v0.25.4 `tenant_llm` 主键迁移失败导致注册回滚异常

`api/db/db_models.py:1638` 在 `migrate_db()` 里调用 `update_tenant_llm_to_id_primary_key()`。这是 commit `62cb29263 Feat/tenant model (#13072)` 引入的：给 `tenant_llm` 表加自增 `id` 主键，供 `tenant.tenant_llm_id` 等新字段引用。

**PostgreSQL 路径**（`db_models.py:1509-1583`，函数 `_update_tenant_llm_to_id_primary_key_postgres`）：

```sql
0. 检查 tenant_llm 是否已有 id 列；有则直接返回（幂等）
1. ALTER TABLE tenant_llm ADD COLUMN temp_id INTEGER NULL;
2. WITH ordered AS (SELECT ctid, ROW_NUMBER() OVER (ORDER BY tenant_id, llm_factory, llm_name) AS rn FROM tenant_llm)
   UPDATE tenant_llm SET temp_id = ordered.rn FROM ordered WHERE tenant_llm.ctid = ordered.ctid;
3. ALTER TABLE tenant_llm DROP CONSTRAINT "<旧主键名>";        -- 危险点
4. ALTER TABLE tenant_llm ALTER COLUMN temp_id SET NOT NULL;
   CREATE SEQUENCE IF NOT EXISTS tenant_llm_id_seq;
   SELECT setval('tenant_llm_id_seq', COALESCE((SELECT MAX(temp_id) FROM tenant_llm), 0));
   ALTER TABLE tenant_llm ALTER COLUMN temp_id SET DEFAULT nextval('tenant_llm_id_seq');
   ALTER SEQUENCE tenant_llm_id_seq OWNED BY tenant_llm.temp_id;
   ALTER TABLE tenant_llm ADD PRIMARY KEY (temp_id);
5. ALTER TABLE tenant_llm ADD CONSTRAINT uk_tenant_llm UNIQUE (tenant_id, llm_factory, llm_name);
6. ALTER TABLE tenant_llm RENAME COLUMN temp_id TO id;
```

**致命点**：第 3 步已经 DROP 了原主键约束。如果第 4 步或第 5 步失败（如升级前 `tenant_llm` 表里 `(tenant_id, llm_factory, llm_name)` 有重复行，或 sequence 创建失败），整张表会留在"无主键"的状态。except 块（`db_models.py:1572-1583`）只会检查并清理 `temp_id` 列，**不会恢复原 PK**。

**对注册流程的连锁影响**（`user_account_service.py:92-140`）：

```python
if not UserService.save(**user_info):
    return {"success": False}
TenantService.insert(**tenant)
UserTenantService.insert(**usr_tenant)
TenantLLMService.insert_many(tenant_llm)   # 在坏表上失败
FileService.insert(file)
```

进入 except 块回滚（每步独立 try/except）：

```python
TenantService.delete_by_id(user_id)       # 成功：tenant 删了
...
UserService.delete_by_id(user_id)         # 若这步也失败，user 残留
```

**只要 `UserService.delete_by_id` 失败（外键约束 / DB 抖动 / 部分表迁移失败），就会留下"有 user、无 tenant"的僵尸账号** —— 登录能成功，但任何需要 tenant 的操作都报 "Tenant not found"。

### 原因 3：登录绕过了正常注册流程（少见）

某些 SSO / OAuth 路径如果单独写了 user 但没建 tenant。RAGFlow 默认密码登录走 `user_account_service.create_user`，会原子地建 tenant。需检查是否启用了第三方登录。

## 诊断 SQL

### 1. 确认是哪一种缺失

```sql
SELECT u.id, u.email, u.create_time,
       (SELECT COUNT(*) FROM tenant       WHERE id = u.id)       AS tenant_exists,
       (SELECT COUNT(*) FROM user_tenant  WHERE user_id = u.id)  AS user_tenant_exists,
       (SELECT COUNT(*) FROM api_token   WHERE tenant_id = u.id) AS api_token_count
FROM "user" u
ORDER BY u.create_time;
```

判读：
- 所有用户 `tenant_exists = 0` → **原因 1**（DB 整体不对）
- 个别用户 `tenant_exists = 0` → **原因 2**（注册回滚异常）
- `user_tenant_exists = 0` 但 `tenant_exists = 1` → user_tenant 关联表丢失
- 全部 `= 1` 但仍报 "Tenant not found" → **本表下方"高级诊断"**

### 1.5 高级诊断：tenant_exists = 1 仍报 "Tenant not found"

如果上一步显示 tenant 行存在但仍报错，说明 `get_by_id` 内部出了状况。按以下顺序排查：

**a) 看日志有没有堆栈**：在 `error:root:Tenant not found.` 这行后面
- 有 Traceback → DB 列/类型不匹配，跳到诊断 2（检查 tenant_llm），同时检查 tenant 表 schema：

  ```sql
  -- 列出 tenant 表所有列
  SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
  FROM information_schema.columns
  WHERE table_schema = current_schema() AND table_name = 'tenant'
  ORDER BY ordinal_position;
  ```

  对照 `api/db/db_models.py:736-757` 的 Tenant 模型，看是否有列缺失。

- 无 Traceback → 是 `get_or_none` 真的返回 None，但行存在 → 走 b

**b) 确认报错用户是谁**：

```sql
-- 当前报错用户的 tenant 行直接查
SELECT u.id, u.email, u.is_superuser,
       t.id AS tenant_id, t.llm_id, t.embd_id, t.rerank_id, t.parser_ids, t.status
FROM "user" u
LEFT JOIN tenant t ON u.id = t.id
WHERE u.email = '<报错用户的邮箱>';
```

如果 `tenant_id` 列是 NULL → 行确实不存在（与 SQL 1 矛盾，说明 SQL 1 跑在不同的 schema/database）
如果行存在 → 走 c

**c) 抓真实请求的 tenant_id**：临时在 `api/db/services/common_service.py:288` 加日志

```python
@classmethod
@DB.connection_context()
def get_by_id(cls, pid):
    try:
        logging.warning(f"[DEBUG] TenantService.get_by_id pid={pid!r} type={type(pid)}")
        obj = cls.model.get_or_none(cls.model.id == pid)
        logging.warning(f"[DEBUG] TenantService.get_by_id result={obj}")
        if obj:
            return True, obj
    except Exception as e:
        logging.exception(f"[DEBUG] TenantService.get_by_id EXCEPTION: {e}")
    return False, None
```

重启服务，触发一次创建 KB，看日志里实际传入的 `pid` 是什么。常见情况：
- `pid=None` → `current_user.id` 为空 → 走查 token/session 路径
- `pid='某 id'` 且 `result=None` → id 确实不匹配（**最可能：报错用户与 SQL 1 检查的用户不是同一个**）
- `EXCEPTION` → 看 Traceback 找真正的 DB 错误

### 2. 检查 `tenant_llm` 表结构与主键迁移结果

```sql
-- 查询列定义
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = current_schema()
  AND table_name = 'tenant_llm'
ORDER BY ordinal_position;

-- 查主键约束（应存在，名字通常是 tenant_llm_pkey）
SELECT con.conname AS constraint_name, con.contype
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
WHERE rel.relname = 'tenant_llm'
  AND nsp.nspname = current_schema()
  AND con.contype = 'p';

-- 查 sequence（应该存在 tenant_llm_id_seq）
SELECT sequence_name FROM information_schema.sequences
WHERE sequence_schema = current_schema()
  AND sequence_name = 'tenant_llm_id_seq';

-- psql 快捷方式：\d tenant_llm
```

正确结果：
- 列里应有 `id` 列，`column_default` 类似 `nextval('tenant_llm_id_seq'::regclass)`
- `is_nullable = NO`
- 主键约束存在
- `tenant_llm_id_seq` 序列存在

迁移失败的典型表现：
- 只有 `temp_id` 列、没有 `id` 列 → 第 6 步 RENAME 失败
- 既无 `temp_id` 也无 `id` → except 块清掉了 temp_id，但原 PK 已被第 3 步 DROP
- 主键约束查不到 → 表处于"无主键"状态

### 3. 检查升级前的 `tenant_llm` 是否有重复行

```sql
SELECT tenant_id, llm_factory, llm_name, COUNT(*) cnt
FROM tenant_llm
GROUP BY tenant_id, llm_factory, llm_name
HAVING cnt > 1;
```

有重复行 → 迁移第 5 步必然失败，证实原因 2。

### 4. 查 ragflow_server.log 关键行

```bash
grep -E "Successfully updated tenant_llm|create_error|Tenant not found" \
  /ragflow/log/ragflow_server.log
```

- `Successfully updated tenant_llm to id primary key.` → 迁移成功（排除原因 2 主流程）
- 任何 `logging.exception(create_error)` 堆栈 → 注册时回滚过

## 修复方案

### 按原因分别处理

#### 原因 1（DB 整体没迁好）

恢复正确的 MySQL 卷 / 重新挂载旧卷。修复后重跑诊断 SQL 1 确认。

#### 原因 2（`tenant_llm` 表坏了 + 个别僵尸用户）

**Step A：修 `tenant_llm` 表**

先清理重复行（PG 用 `ctid`）：

```sql
-- 重复行先看一下
SELECT tenant_id, llm_factory, llm_name, COUNT(*) cnt
FROM tenant_llm
GROUP BY tenant_id, llm_factory, llm_name
HAVING COUNT(*) > 1;

-- 用 ctid 去重，每组保留 ctid 最小的一行
DELETE FROM tenant_llm
WHERE ctid NOT IN (
    SELECT MIN(ctid)
    FROM tenant_llm
    GROUP BY tenant_id, llm_factory, llm_name
);
```

**视当前表状态选择修复路径**：

**情况 ①：表已无主键、也无 `id`/`temp_id` 列**（最干净的失败状态）

直接加 `SERIAL` 主键，PG 会自动建 sequence + NOT NULL + PK：

```sql
BEGIN;
ALTER TABLE tenant_llm ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE tenant_llm ADD CONSTRAINT uk_tenant_llm UNIQUE (tenant_id, llm_factory, llm_name);
COMMIT;
```

注意：`SERIAL` 按 PostgreSQL 内部顺序生成 id，不一定与原迁移脚本设定的 `(tenant_id, llm_factory, llm_name)` 排序一致。只要后续 `tenant.tenant_llm_id` 等字段都是 NULL（升级后还没填），就无所谓。

**情况 ②：残留 `temp_id` 列、原 PK 已丢**

```sql
BEGIN;
-- 回到干净状态
ALTER TABLE tenant_llm DROP COLUMN IF EXISTS temp_id;

-- 按原迁移脚本顺序重新加 id（如果想保持有序）
ALTER TABLE tenant_llm ADD COLUMN id INTEGER;
CREATE SEQUENCE IF NOT EXISTS tenant_llm_id_seq;

WITH ordered AS (
    SELECT ctid,
           ROW_NUMBER() OVER (ORDER BY tenant_id, llm_factory, llm_name) AS rn
    FROM tenant_llm
)
UPDATE tenant_llm t
SET id = o.rn
FROM ordered o
WHERE t.ctid = o.ctid;

SELECT setval('tenant_llm_id_seq',
              COALESCE((SELECT MAX(id) FROM tenant_llm), 0));
ALTER TABLE tenant_llm ALTER COLUMN id SET DEFAULT nextval('tenant_llm_id_seq');
ALTER TABLE tenant_llm ALTER COLUMN id SET NOT NULL;
ALTER TABLE tenant_llm ADD CONSTRAINT tenant_llm_pkey PRIMARY KEY (id);
ALTER SEQUENCE tenant_llm_id_seq OWNED BY tenant_llm.id;
ALTER TABLE tenant_llm ADD CONSTRAINT uk_tenant_llm UNIQUE (tenant_id, llm_factory, llm_name);

COMMIT;
```

**情况 ③：表已经正常（有 `id`、有主键），但 sequence 没建对**

```sql
-- 修复 sequence 当前值，避免下个 INSERT 唯一冲突
SELECT setval('tenant_llm_id_seq',
              COALESCE((SELECT MAX(id) FROM tenant_llm), 0));
```

修完后，再次跑诊断 SQL 2 确认结构正确。

**Step B：处理僵尸用户**

最简单的办法是删除僵尸用户，让他们重新注册（`tenant_llm` 已修复后注册不会再失败）：

```sql
-- 先确认这些用户确实没 tenant
SELECT u.id, u.email FROM user u
LEFT JOIN tenant t ON u.id = t.id
WHERE t.id IS NULL;

-- 删除（注意：会丢失这些用户的历史数据，先评估）
DELETE FROM user WHERE id IN (...);
DELETE FROM user_tenant WHERE user_id IN (...);
```

如果用户数据宝贵：手动补建 tenant 行（参考 `user_account_service.py:64-79` 的字段），并保证 `llm_id`、`embd_id`、`asr_id`、`img2txt_id`、`rerank_id`、`parser_ids` 有合理默认值。

#### 原因 3（SSO 路径漏建）

补建 tenant 行 + user_tenant 行（同上）。

## OTel exporter 错误的相关性

**与本问题无关。**

- OTel exporter 是把 trace 数据推送到 collector，超时通常因为离线环境 collector 不可达
- 异步后台导出，失败只影响 trace 可观测性，不阻塞业务逻辑、不改变 DB 查询结果

**消噪**：在 `docker/.env` 设置

```
OTEL_SDK_DISABLED=true
# 或
OTEL_EXPORTER_OTLP_ENDPOINT=
```

## 关键文件索引

| 文件 | 作用 |
|---|---|
| `api/db/services/knowledgebase_service.py:420-422` | KB 创建时的 tenant 校验 |
| `api/db/services/common_service.py:281-293` | `get_by_id` 实现（只按 id 查） |
| `api/utils/api_utils.py:236-244` | `add_tenant_id_to_kwargs` 装饰器 |
| `api/apps/__init__.py:129-191` | `_load_user` / `current_user` 解析 |
| `api/db/joint_services/user_account_service.py:50-140` | 用户注册（含回滚逻辑） |
| `api/db/db_models.py:736-757` | `Tenant` 表模型 |
| `api/db/db_models.py:1455-1506` | MySQL 版 `tenant_llm` 主键迁移 |
| `api/db/db_models.py:1509-1583` | **PostgreSQL 版** `tenant_llm` 主键迁移 |
| `api/db/db_models.py:1585-1658` | `migrate_db()` 主入口 |

## 经验沉淀

1. **报错字符串带不带句号、大小写都能定位代码**：本次 `Tenant not found.`（带句号、首字母大写）只有 2 处匹配，配合业务场景（KB 创建）立刻锁定。
2. **追溯 tenant_id 来源时一定要追到头**：发现 `tenant_id == current_user.id` 这条不变量后，"Tenant not found" 等价于"数据库里 tenant 表缺这行"，问题范围立刻收窄。
3. **注册流程的非原子回滚是潜在陷阱**：用多个独立 try/except 做补偿，单步失败就会留下半残数据。看注册代码时不能只看 happy path。
4. **升级相关的"数据丢失"问题，先怀疑数据卷和 DB 连接，再怀疑迁移脚本**：迁移脚本通常 idempotent，DB 路径错配才是大头。
5. **`get_data_error_result` 这类 helper 不只是构造响应**：它还顺带记日志。看到 `error:root:<message>` 格式时，grep `get_data_error_result(message=` 能反查到具体的调用点。
6. **`except Exception: pass` 是 "Tenant not found" 类错误的放大器**：DB 异常被吞，外层看到的全是 "not found"。诊断时要先加 logging.exception 把真实异常打出来再判断。
7. **SQL 显示行存在但仍报 not found 时，要并行查"日志有没有堆栈"和"实际传入的 pid 是什么"**：这两个信号能区分是数据问题还是 schema 问题，避免在错误方向上耗时。
