# RAGFlow 升级后 "Tenant not found" 定位文档

## 背景

- **场景**：离线服务器将 RAGFlow 从 0.23.0 升级到 0.25.4
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

### `get_by_id` 仅按 id 过滤

`api/db/services/common_service.py:288`：

```python
obj = cls.model.get_or_none(cls.model.id == pid)
```

无 status、无其他过滤。所以 "not found" 等价于 **`tenant` 表中没有该 id 的行**。

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

**MySQL 路径**（`db_models.py:1455-1506`）：

```sql
1. ALTER TABLE tenant_llm ADD COLUMN temp_id INT NULL;
2. UPDATE tenant_llm SET temp_id = (@row := @row + 1) ORDER BY tenant_id, llm_factory, llm_name;
3. ALTER TABLE tenant_llm DROP PRIMARY KEY;                    -- 危险点
4. ALTER TABLE tenant_llm MODIFY COLUMN temp_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY;
5. ALTER TABLE tenant_llm ADD CONSTRAINT uk_tenant_llm UNIQUE (tenant_id, llm_factory, llm_name);
6. ALTER TABLE tenant_llm RENAME COLUMN temp_id TO id;
```

**致命点**：第 3 步已经 DROP 了原主键。如果第 4 步或第 5 步失败（如升级前 `tenant_llm` 表里 `(tenant_id, llm_factory, llm_name)` 有重复行），整张表会留在"无主键"的状态。except 块只会清理 `temp_id` 列，不会恢复原 PK。

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
       (SELECT COUNT(*) FROM user_tenant  WHERE user_id = u.id)  AS user_tenant_exists
FROM user u;
```

判读：
- 所有用户 `tenant_exists = 0` → **原因 1**（DB 整体不对）
- 个别用户 `tenant_exists = 0` → **原因 2**（注册回滚异常）
- `user_tenant_exists = 0` 但 `tenant_exists = 1` → user_tenant 关联表丢失

### 2. 检查 `tenant_llm` 主键迁移结果

```sql
DESCRIBE tenant_llm;
```

正确结果应包含：`id INT NOT NULL AUTO_INCREMENT PRIMARY KEY`。

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

先清理重复行：

```sql
DELETE t1 FROM tenant_llm t1
INNER JOIN tenant_llm t2
WHERE t1.ctid < t2.ctid  -- MySQL 用：t1.id < t2.id 自连接，保留一条
  AND t1.tenant_id = t2.tenant_id
  AND t1.llm_factory = t2.llm_factory
  AND t1.llm_name = t2.llm_name;
```

再手动加自增主键：

```sql
ALTER TABLE tenant_llm ADD COLUMN id INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST;
ALTER TABLE tenant_llm ADD CONSTRAINT uk_tenant_llm UNIQUE (tenant_id, llm_factory, llm_name);
```

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
| `api/db/db_models.py:1585-1658` | `migrate_db()` 主入口 |

## 经验沉淀

1. **报错字符串带不带句号、大小写都能定位代码**：本次 `Tenant not found.`（带句号、首字母大写）只有 2 处匹配，配合业务场景（KB 创建）立刻锁定。
2. **追溯 tenant_id 来源时一定要追到头**：发现 `tenant_id == current_user.id` 这条不变量后，"Tenant not found" 等价于"数据库里 tenant 表缺这行"，问题范围立刻收窄。
3. **注册流程的非原子回滚是潜在陷阱**：用多个独立 try/except 做补偿，单步失败就会留下半残数据。看注册代码时不能只看 happy path。
4. **升级相关的"数据丢失"问题，先怀疑数据卷和 DB 连接，再怀疑迁移脚本**：迁移脚本通常 idempotent，DB 路径错配才是大头。
