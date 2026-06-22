# RAGFlow Tenant not Found - 本轮定位命令

## 判读当前线索

- 日志只有一行 `error:root:Tenant not found.` 无堆栈 → `get_by_id` 走 happy path 返回 None
- SQL #3 报错用户行查询返回"不是 null 是 false" → **该用户 tenant 行确实不存在**（之前 SQL 1 看的是管理员账号）
- 所有用户都通过 web UI 登录，不走 API token

结论方向：**部分用户缺少 tenant 行**。本轮目标是定位到这些用户并补建数据。

---

## Step 1：列出所有缺 tenant 行的用户

```sql
-- 1.1 缺 tenant 行的用户
SELECT u.id AS user_id, u.email, u.nickname, u.create_time, u.last_login_time,
       (SELECT COUNT(*) FROM tenant       WHERE id = u.id)       AS tenant_exists,
       (SELECT COUNT(*) FROM user_tenant  WHERE user_id = u.id)  AS user_tenant_exists
FROM "user" u
WHERE NOT EXISTS (SELECT 1 FROM tenant WHERE id = u.id)
ORDER BY u.create_time;

-- 1.2 缺 user_tenant 行的用户（补漏）
SELECT u.id AS user_id, u.email,
       (SELECT COUNT(*) FROM tenant       WHERE id = u.id)       AS tenant_exists,
       (SELECT COUNT(*) FROM user_tenant  WHERE user_id = u.id)  AS user_tenant_exists
FROM "user" u
WHERE NOT EXISTS (SELECT 1 FROM user_tenant WHERE user_id = u.id)
ORDER BY u.create_time;
```

**判读**：
- 1.1 有结果 → 这些用户缺 tenant 行，走 Step 2
- 1.1 无结果但 1.2 有结果 → 缺 user_tenant 关联
- 都为空 → 走 Step 4 加调试日志抓真实 pid

---

## Step 2：找一个"好"的 tenant 行作为模板

```sql
-- 取一个正常的 tenant 行（一般是管理员），后续 INSERT 用它的模型配置
SELECT id, name, llm_id, embd_id, asr_id, img2txt_id, rerank_id, tts_id, parser_ids
FROM tenant
ORDER BY create_time ASC
LIMIT 3;
```

记下其中一行的 `id`（下面 `<template_tenant_id>` 用），以及 `llm_id`、`embd_id`、`asr_id`、`img2txt_id`、`rerank_id`、`tts_id`、`parser_ids` 的值。

---

## Step 3：批量补建缺失的 tenant / user_tenant 行

**先 dry-run 看会插入什么**：

```sql
-- 预览将插入的 tenant 行
SELECT
    u.id                                                                 AS new_tenant_id,
    COALESCE(u.nickname, split_part(u.email, '@', 1)) || '''s Kingdom'    AS name,
    tmpl.llm_id, tmpl.embd_id, tmpl.asr_id, tmpl.img2txt_id,
    tmpl.rerank_id, tmpl.tts_id, tmpl.parser_ids,
    512                                                                  AS credit,
    '1'                                                                  AS status,
    (EXTRACT(EPOCH FROM NOW()) * 1000)::BIGINT                           AS create_time,
    (EXTRACT(EPOCH FROM NOW()) * 1000)::BIGINT                           AS update_time
FROM "user" u
CROSS JOIN tenant tmpl
WHERE tmpl.id = '<template_tenant_id>'           -- ← 替换成 Step 2 拿到的模板 id
  AND NOT EXISTS (SELECT 1 FROM tenant WHERE id = u.id);
```

**确认无误后执行真正的 INSERT**（一个事务，方便回滚）：

```sql
BEGIN;

-- 3.1 补 tenant 行
INSERT INTO tenant (
    id, name,
    llm_id, embd_id, asr_id, img2txt_id, rerank_id, tts_id, parser_ids,
    credit, status, create_time, update_time
)
SELECT
    u.id,
    COALESCE(u.nickname, split_part(u.email, '@', 1)) || '''s Kingdom',
    tmpl.llm_id, tmpl.embd_id, tmpl.asr_id, tmpl.img2txt_id,
    tmpl.rerank_id, tmpl.tts_id, tmpl.parser_ids,
    512, '1',
    (EXTRACT(EPOCH FROM NOW()) * 1000)::BIGINT,
    (EXTRACT(EPOCH FROM NOW()) * 1000)::BIGINT
FROM "user" u
CROSS JOIN tenant tmpl
WHERE tmpl.id = '<template_tenant_id>'           -- ← 替换
  AND NOT EXISTS (SELECT 1 FROM tenant WHERE id = u.id);

-- 3.2 补 user_tenant 行（owner 角色）
INSERT INTO user_tenant (
    id, user_id, tenant_id, role, invited_by, status, create_time, update_time
)
SELECT
    gen_random_uuid()::text,                           -- id 用伪 UUID
    u.id, u.id,
    'owner',                                            -- UserTenantRole.OWNER
    u.id,
    '1',
    (EXTRACT(EPOCH FROM NOW()) * 1000)::BIGINT,
    (EXTRACT(EPOCH FROM NOW()) * 1000)::BIGINT
FROM "user" u
WHERE NOT EXISTS (SELECT 1 FROM user_tenant WHERE user_id = u.id);

-- 3.3 验证
SELECT count(*) AS missing_tenant_now
FROM "user" u
WHERE NOT EXISTS (SELECT 1 FROM tenant WHERE id = u.id);

-- 如果 missing_tenant_now = 0，提交；否则 ROLLBACK
COMMIT;
-- 如果不对：ROLLBACK;
```

**注意**：`gen_random_uuid()` 需要 PG 13+（默认内置）。若报错"function gen_random_uuid does not exist"，先跑：
```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```
或把 `gen_random_uuid()::text` 替换为 `md5(random()::text || clock_timestamp()::text)`。

---

## Step 4（可选）：Step 1 都查不到才需要 - 加调试日志抓真实 pid

如果 Step 1.1 和 1.2 都为空（说明所有用户都有 tenant 行，但仍报错），需要抓实际请求里传入的 tenant_id。

### 4.1 修改文件

文件：`api/db/services/common_service.py`，找到 `def get_by_id`（约 281 行），把函数体替换为：

```python
    @classmethod
    @DB.connection_context()
    def get_by_id(cls, pid):
        try:
            logging.warning(f"[DEBUG] get_by_id cls={cls.__name__} pid={pid!r} type={type(pid).__name__}")
            obj = cls.model.get_or_none(cls.model.id == pid)
            logging.warning(f"[DEBUG] get_by_id cls={cls.__name__} result={'HIT' if obj else 'MISS'}")
            if obj:
                return True, obj
        except Exception as e:
            logging.exception(f"[DEBUG] get_by_id cls={cls.__name__} EXCEPTION: {e}")
        return False, None
```

### 4.2 容器内重启 ragflow_server

容器名假设是 `ragflow-server`（用 `docker ps --filter "name=ragflow"` 确认）。三种方式任选：

```bash
# 方式 A：整个容器重启（最简单，约 30-60s）
docker restart ragflow-server

# 方式 B：只重启进程（更快，10-20s，不丢其它服务）
docker exec -it ragflow-server supervisorctl restart ragflow_server

# 方式 C：进容器手动操作
docker exec -it ragflow-server bash
# 容器内：
supervisorctl status                       # 看 ragflow_server 当前状态
supervisorctl restart ragflow_server       # 重启
tail -f /ragflow/log/ragflow_server.log    # 跟日志
```

### 4.3 触发并抓日志

web UI 触发一次创建 KB，然后：

```bash
docker exec -it ragflow-server bash -c \
  "grep -E 'DEBUG get_by_id|Tenant not found' /ragflow/log/ragflow_server.log | tail -40"
```

把这段输出贴出来。重点看：
- `cls=TenantService pid=<值>` 的值
- `result=HIT` 还是 `MISS`
- 有没有 `EXCEPTION`

### 4.4 还原代码

定位完成后，把 `common_service.py` 改回原样并重启：

```python
    @classmethod
    @DB.connection_context()
    def get_by_id(cls, pid):
        try:
            obj = cls.model.get_or_none(cls.model.id == pid)
            if obj:
                return True, obj
        except Exception:
            pass
        return False, None
```

重启同 4.2。

---

## Step 5：验证修复

补完 tenant 行后，**让受影响用户在浏览器里彻底退出登录再重登**（清掉 localStorage 里的旧 token），然后创建知识库。

```sql
-- 验证用 SQL：受影响用户现在应该都有 tenant 行了
SELECT u.id, u.email,
       (SELECT COUNT(*) FROM tenant       WHERE id = u.id)      AS tenant_exists,
       (SELECT COUNT(*) FROM user_tenant  WHERE user_id = u.id) AS user_tenant_exists
FROM "user" u
ORDER BY u.create_time;
```
