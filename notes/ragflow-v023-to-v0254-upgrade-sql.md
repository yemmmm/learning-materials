# RAGFlow v0.23 → v0.25.4 数据库升级 SQL（PostgreSQL）

## 背景

从 RAGFlow v0.23 升级到 v0.25.4 时，数据库 schema 有大量变更。
内置的 `migrate_db()` 函数（`api/db/db_models.py:1585`）虽然在启动时自动执行，
但存在 `logging.disable(logging.ERROR)` 压制所有错误日志的问题，
导致迁移失败时无任何提示，只能通过 web 页面报错被动发现。

本文档整理了所有需要执行的 SQL，按表分组。每条语句使用了 `IF NOT EXISTS`
或等效的幂等写法，可重复执行。

---

## 1. tenant_llm 表主键变更（核心变更）

```sql
-- v0.23: 复合主键 (tenant_id, llm_factory, llm_name)，无 id 列
-- v0.25: id SERIAL PRIMARY KEY + UNIQUE(tenant_id, llm_factory, llm_name)

DO $$
DECLARE
    old_pk_name TEXT;
BEGIN
    -- 检查是否已迁移
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tenant_llm' AND column_name = 'id'
    ) THEN
        RAISE NOTICE 'tenant_llm.id already exists, skipping migration';
        RETURN;
    END IF;

    -- 1. 添加临时 id 列
    ALTER TABLE tenant_llm ADD COLUMN temp_id INTEGER;

    -- 2. 填充序号
    UPDATE tenant_llm SET temp_id = subq.rn FROM (
        SELECT ctid, ROW_NUMBER() OVER (ORDER BY tenant_id, llm_factory, llm_name) AS rn
        FROM tenant_llm
    ) AS subq
    WHERE tenant_llm.ctid = subq.ctid;

    -- 3. 删除旧复合主键
    SELECT constraint_name INTO old_pk_name
    FROM information_schema.table_constraints
    WHERE table_name = 'tenant_llm' AND constraint_type = 'PRIMARY KEY';
    IF old_pk_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE tenant_llm DROP CONSTRAINT "' || old_pk_name || '"';
    END IF;

    -- 4. 设置新主键
    ALTER TABLE tenant_llm ALTER COLUMN temp_id SET NOT NULL;
    CREATE SEQUENCE IF NOT EXISTS tenant_llm_id_seq;
    PERFORM setval('tenant_llm_id_seq', COALESCE((SELECT MAX(temp_id) FROM tenant_llm), 0));
    ALTER TABLE tenant_llm ALTER COLUMN temp_id SET DEFAULT nextval('tenant_llm_id_seq');
    ALTER SEQUENCE tenant_llm_id_seq OWNED BY tenant_llm.temp_id;
    ALTER TABLE tenant_llm ADD PRIMARY KEY (temp_id);

    -- 5. 唯一约束
    ALTER TABLE tenant_llm ADD CONSTRAINT uk_tenant_llm UNIQUE (tenant_id, llm_factory, llm_name);

    -- 6. 重命名
    ALTER TABLE tenant_llm RENAME COLUMN temp_id TO id;

    RAISE NOTICE 'tenant_llm primary key migration completed';
END $$;
```

---

## 2. 新增列 — 按表分组

### 2.1 tenant 表

```sql
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS rerank_id      VARCHAR(128) DEFAULT 'BAAI/bge-reranker-v2-m3';
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tts_id         VARCHAR(256);
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_llm_id     INTEGER;
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_embd_id    INTEGER;
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_asr_id     INTEGER;
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_img2txt_id INTEGER;
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_rerank_id  INTEGER;
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_tts_id     INTEGER;
```

### 2.2 knowledgebase 表

```sql
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS pagerank               INTEGER DEFAULT 0;
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS pipeline_id            VARCHAR(32);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS graphrag_task_id       VARCHAR(32);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS raptor_task_id         VARCHAR(32);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS graphrag_task_finish_at TIMESTAMP;
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS raptor_task_finish_at  VARCHAR(1);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS mindmap_task_id        VARCHAR(32);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS mindmap_task_finish_at VARCHAR(1);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS tenant_embd_id         INTEGER;
```

### 2.3 document 表

```sql
ALTER TABLE document ADD COLUMN IF NOT EXISTS suffix       VARCHAR(32) NOT NULL DEFAULT '';
ALTER TABLE document ADD COLUMN IF NOT EXISTS pipeline_id  VARCHAR(32);
ALTER TABLE document ADD COLUMN IF NOT EXISTS content_hash VARCHAR(32) DEFAULT '';
```

### 2.4 file 表

```sql
ALTER TABLE file ADD COLUMN IF NOT EXISTS source_type VARCHAR(128) NOT NULL DEFAULT '';
```

### 2.5 dialog 表

```sql
ALTER TABLE dialog ADD COLUMN IF NOT EXISTS rerank_id        VARCHAR(128) DEFAULT '';
ALTER TABLE dialog ADD COLUMN IF NOT EXISTS meta_data_filter TEXT DEFAULT '{}';
ALTER TABLE dialog ADD COLUMN IF NOT EXISTS tenant_llm_id    INTEGER;
ALTER TABLE dialog ADD COLUMN IF NOT EXISTS tenant_rerank_id INTEGER;
```

### 2.6 task 表

```sql
ALTER TABLE task ADD COLUMN IF NOT EXISTS retry_count  INTEGER DEFAULT 0;
ALTER TABLE task ADD COLUMN IF NOT EXISTS digest       TEXT DEFAULT '';
ALTER TABLE task ADD COLUMN IF NOT EXISTS chunk_ids    TEXT DEFAULT '';
ALTER TABLE task ADD COLUMN IF NOT EXISTS task_type    VARCHAR(32) NOT NULL DEFAULT '';
ALTER TABLE task ADD COLUMN IF NOT EXISTS priority     INTEGER DEFAULT 0;
```

### 2.7 tenant_llm 表（新增属性列，不含主键变更）

```sql
ALTER TABLE tenant_llm ADD COLUMN IF NOT EXISTS api_key    TEXT;
ALTER TABLE tenant_llm ADD COLUMN IF NOT EXISTS max_tokens INTEGER DEFAULT 8192;
ALTER TABLE tenant_llm ADD COLUMN IF NOT EXISTS status     VARCHAR(1) NOT NULL DEFAULT '1';
```

### 2.8 api_token 表

```sql
ALTER TABLE api_token ADD COLUMN IF NOT EXISTS source VARCHAR(16);
ALTER TABLE api_token ADD COLUMN IF NOT EXISTS beta   VARCHAR(255);
```

### 2.9 api_4_conversation 表

```sql
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS source        VARCHAR(16);
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS dsl           TEXT DEFAULT '{}';
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS errors        TEXT;
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS name          VARCHAR(255);
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS exp_user_id   VARCHAR(255);
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS version_title VARCHAR(255);
```

### 2.10 conversation 表

```sql
ALTER TABLE conversation ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
```

### 2.11 user_canvas 表

```sql
ALTER TABLE user_canvas ADD COLUMN IF NOT EXISTS permission      VARCHAR(16)  NOT NULL DEFAULT 'me';
ALTER TABLE user_canvas ADD COLUMN IF NOT EXISTS canvas_category VARCHAR(32)  NOT NULL DEFAULT 'agent_canvas';
ALTER TABLE user_canvas ADD COLUMN IF NOT EXISTS tags            VARCHAR(512) NOT NULL DEFAULT '';
ALTER TABLE user_canvas ADD COLUMN IF NOT EXISTS release         BOOLEAN      NOT NULL DEFAULT FALSE;
```

### 2.12 canvas_template 表

```sql
ALTER TABLE canvas_template ADD COLUMN IF NOT EXISTS canvas_category VARCHAR(32) NOT NULL DEFAULT 'agent_canvas';
ALTER TABLE canvas_template ADD COLUMN IF NOT EXISTS canvas_types    TEXT;
```

### 2.13 user_canvas_version 表

```sql
ALTER TABLE user_canvas_version ADD COLUMN IF NOT EXISTS release BOOLEAN NOT NULL DEFAULT FALSE;
```

### 2.14 llm 表

```sql
ALTER TABLE llm ADD COLUMN IF NOT EXISTS is_tools BOOLEAN NOT NULL DEFAULT FALSE;
```

### 2.15 llm_factories 表

```sql
ALTER TABLE llm_factories ADD COLUMN IF NOT EXISTS rank INTEGER DEFAULT 0;
```

### 2.16 mcp_server 表

```sql
ALTER TABLE mcp_server ADD COLUMN IF NOT EXISTS variables TEXT DEFAULT '{}';
```

### 2.17 memory 表

```sql
ALTER TABLE memory ADD COLUMN IF NOT EXISTS tenant_embd_id INTEGER;
ALTER TABLE memory ADD COLUMN IF NOT EXISTS tenant_llm_id  INTEGER;
```

### 2.18 connector2kb 表

```sql
ALTER TABLE connector2kb ADD COLUMN IF NOT EXISTS auto_parse VARCHAR(1) NOT NULL DEFAULT '1';
```

---

## 3. 列类型变更

```sql
-- dialog.top_k: 扩大为 INTEGER
ALTER TABLE dialog ALTER COLUMN top_k TYPE INTEGER;

-- tenant_llm.api_key: VARCHAR → TEXT
ALTER TABLE tenant_llm ALTER COLUMN api_key TYPE TEXT;

-- system_settings.value: VARCHAR → TEXT
ALTER TABLE system_settings ALTER COLUMN value TYPE TEXT;

-- document.size: INTEGER → BIGINT
ALTER TABLE document ALTER COLUMN size TYPE BIGINT;

-- file.size: INTEGER → BIGINT
ALTER TABLE file ALTER COLUMN size TYPE BIGINT;

-- canvas_template.title: VARCHAR → JSON (TEXT)
ALTER TABLE canvas_template ALTER COLUMN title TYPE TEXT;
ALTER TABLE canvas_template ALTER COLUMN description TYPE TEXT;

-- api_token.dialog_id: 改为 VARCHAR(32) NULL
ALTER TABLE api_token ALTER COLUMN dialog_id TYPE VARCHAR(32);
ALTER TABLE api_token ALTER COLUMN dialog_id DROP NOT NULL;
```

---

## 4. 列重命名（仅 v0.22 以下需要，v0.23+ 跳过）

v0.23 起这两列已经叫 `process_duration`，以下 SQL 仅在列名仍为 `process_duation` 时才执行：

```sql
-- 仅在 process_duation 列存在时才重命名
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'task' AND column_name = 'process_duation') THEN
        ALTER TABLE task RENAME COLUMN process_duation TO process_duration;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'document' AND column_name = 'process_duation') THEN
        ALTER TABLE document RENAME COLUMN process_duation TO process_duration;
    END IF;
END $$;
```

---

## 5. user.email 唯一约束

```sql
-- 先清理重复邮箱（保留最早/管理员记录，其余重命名）
DO $$
DECLARE
    dup_record RECORD;
    keep_uid    TEXT;
    dup_uid     TEXT;
BEGIN
    FOR dup_record IN
        SELECT email, COUNT(*) AS cnt
        FROM "user"
        GROUP BY email
        HAVING COUNT(*) > 1
    LOOP
        -- 保留 superuser 或最早的记录
        SELECT id INTO keep_uid FROM "user"
        WHERE email = dup_record.email
        ORDER BY is_superuser DESC, create_time ASC LIMIT 1;

        FOR dup_uid IN
            SELECT id FROM "user"
            WHERE email = dup_record.email AND id != keep_uid
        LOOP
            UPDATE "user"
            SET email = email || '_DUPLICATE_' || left(dup_uid, 8)
            WHERE id = dup_uid;
            RAISE NOTICE 'Renamed duplicate email for user %', dup_uid;
        END LOOP;
    END LOOP;
END $$;

-- 添加唯一索引
CREATE UNIQUE INDEX IF NOT EXISTS user_email ON "user" (email);
```

---

## 使用说明

1. 先备份数据库
2. 按顺序执行上述 SQL（1→2→3→4→5）
3. 每条用了 `IF NOT EXISTS`，可以安全重复执行
4. 执行完后重启所有 RAGFlow 容器
