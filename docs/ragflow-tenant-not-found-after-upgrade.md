# RAGFlow Tenant not Found - 本轮定位命令（真实根因：tenant 表缺列）

## 根因确认

调试日志暴露了被 `except Exception: pass` 吞掉的真实异常：

```
t1.tenant_llm_id does not exist
```

即 **`tenant` 表里缺少 v0.25.4 新增的 `tenant_llm_id` 列**（以及大概率还缺其它列）。

升级 SQL 文档 section 2.1 本应加这些列，但显然没执行到位。本轮目标：把 tenant 表以及关联表（knowledgebase、dialog、memory）所有 v0.25.4 新增列一次性补齐。

---

## Step 1：检查 tenant 表当前缺哪些列

```sql
-- 期望返回这 8 列：rerank_id, tts_id, tenant_llm_id, tenant_embd_id,
-- tenant_asr_id, tenant_img2txt_id, tenant_rerank_id, tenant_tts_id
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = current_schema()
  AND table_name = 'tenant'
ORDER BY ordinal_position;
```

对比下面清单，记下缺的列名。

---

## Step 2：一次性补齐所有 v0.25.4 新增列（事务保护）

```sql
BEGIN;

-- 2.1 tenant 表
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS rerank_id         VARCHAR(128) DEFAULT 'BAAI/bge-reranker-v2-m3';
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tts_id            VARCHAR(256);
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_llm_id     INTEGER;
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_embd_id    INTEGER;
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_asr_id     INTEGER;
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_img2txt_id INTEGER;
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_rerank_id  INTEGER;
ALTER TABLE tenant ADD COLUMN IF NOT EXISTS tenant_tts_id     INTEGER;

-- 2.2 knowledgebase 表
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS pagerank                INTEGER DEFAULT 0;
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS pipeline_id             VARCHAR(32);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS graphrag_task_id        VARCHAR(32);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS raptor_task_id          VARCHAR(32);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS graphrag_task_finish_at TIMESTAMP;
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS raptor_task_finish_at   VARCHAR(1);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS mindmap_task_id         VARCHAR(32);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS mindmap_task_finish_at  VARCHAR(1);
ALTER TABLE knowledgebase ADD COLUMN IF NOT EXISTS tenant_embd_id          INTEGER;

-- 2.3 document 表
ALTER TABLE document ADD COLUMN IF NOT EXISTS suffix       VARCHAR(32) NOT NULL DEFAULT '';
ALTER TABLE document ADD COLUMN IF NOT EXISTS pipeline_id  VARCHAR(32);
ALTER TABLE document ADD COLUMN IF NOT EXISTS content_hash VARCHAR(32) DEFAULT '';

-- 2.4 file 表
ALTER TABLE file ADD COLUMN IF NOT EXISTS source_type VARCHAR(128) NOT NULL DEFAULT '';

-- 2.5 dialog 表
ALTER TABLE dialog ADD COLUMN IF NOT EXISTS rerank_id        VARCHAR(128) DEFAULT '';
ALTER TABLE dialog ADD COLUMN IF NOT EXISTS meta_data_filter TEXT DEFAULT '{}';
ALTER TABLE dialog ADD COLUMN IF NOT EXISTS tenant_llm_id    INTEGER;
ALTER TABLE dialog ADD COLUMN IF NOT EXISTS tenant_rerank_id INTEGER;

-- 2.6 task 表
ALTER TABLE task ADD COLUMN IF NOT EXISTS retry_count  INTEGER DEFAULT 0;
ALTER TABLE task ADD COLUMN IF NOT EXISTS digest       TEXT DEFAULT '';
ALTER TABLE task ADD COLUMN IF NOT EXISTS chunk_ids    TEXT DEFAULT '';
ALTER TABLE task ADD COLUMN IF NOT EXISTS task_type    VARCHAR(32) NOT NULL DEFAULT '';
ALTER TABLE task ADD COLUMN IF NOT EXISTS priority     INTEGER DEFAULT 0;

-- 2.7 tenant_llm 表（不含主键变更，主键变更已在 section 1 完成）
ALTER TABLE tenant_llm ADD COLUMN IF NOT EXISTS api_key    TEXT;
ALTER TABLE tenant_llm ADD COLUMN IF NOT EXISTS max_tokens INTEGER DEFAULT 8192;
ALTER TABLE tenant_llm ADD COLUMN IF NOT EXISTS status     VARCHAR(1) NOT NULL DEFAULT '1';

-- 2.8 api_token 表
ALTER TABLE api_token ADD COLUMN IF NOT EXISTS source VARCHAR(16);
ALTER TABLE api_token ADD COLUMN IF NOT EXISTS beta   VARCHAR(255);

-- 2.9 api_4_conversation 表
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS source        VARCHAR(16);
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS dsl           TEXT DEFAULT '{}';
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS errors        TEXT;
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS name          VARCHAR(255);
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS exp_user_id   VARCHAR(255);
ALTER TABLE api_4_conversation ADD COLUMN IF NOT EXISTS version_title VARCHAR(255);

-- 2.10 conversation 表
ALTER TABLE conversation ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- 2.11 user_canvas 表
ALTER TABLE user_canvas ADD COLUMN IF NOT EXISTS permission      VARCHAR(16)  NOT NULL DEFAULT 'me';
ALTER TABLE user_canvas ADD COLUMN IF NOT EXISTS canvas_category VARCHAR(32)  NOT NULL DEFAULT 'agent_canvas';
ALTER TABLE user_canvas ADD COLUMN IF NOT EXISTS tags            VARCHAR(512) NOT NULL DEFAULT '';
ALTER TABLE user_canvas ADD COLUMN IF NOT EXISTS release         BOOLEAN      NOT NULL DEFAULT FALSE;

-- 2.12 canvas_template 表
ALTER TABLE canvas_template ADD COLUMN IF NOT EXISTS canvas_category VARCHAR(32) NOT NULL DEFAULT 'agent_canvas';
ALTER TABLE canvas_template ADD COLUMN IF NOT EXISTS canvas_types    TEXT;

-- 2.13 user_canvas_version 表
ALTER TABLE user_canvas_version ADD COLUMN IF NOT EXISTS release BOOLEAN NOT NULL DEFAULT FALSE;

-- 2.14 llm 表
ALTER TABLE llm ADD COLUMN IF NOT EXISTS is_tools BOOLEAN NOT NULL DEFAULT FALSE;

-- 2.15 llm_factories 表
ALTER TABLE llm_factories ADD COLUMN IF NOT EXISTS rank INTEGER DEFAULT 0;

-- 2.16 mcp_server 表
ALTER TABLE mcp_server ADD COLUMN IF NOT EXISTS variables TEXT DEFAULT '{}';

-- 2.17 memory 表
ALTER TABLE memory ADD COLUMN IF NOT EXISTS tenant_embd_id INTEGER;
ALTER TABLE memory ADD COLUMN IF NOT EXISTS tenant_llm_id  INTEGER;

-- 2.18 connector2kb 表
ALTER TABLE connector2kb ADD COLUMN IF NOT EXISTS auto_parse VARCHAR(1) NOT NULL DEFAULT '1';

-- 验证：tenant_llm_id 列现在应该存在
SELECT column_name FROM information_schema.columns
WHERE table_schema = current_schema() AND table_name = 'tenant' AND column_name = 'tenant_llm_id';

COMMIT;
-- 若任意一步报错：ROLLBACK;
```

PG 支持 DDL 事务，整段任何一条失败就 `ROLLBACK` 全部回滚。

---

## Step 3：列类型变更（也建议一并执行，避免后续踩坑）

```sql
BEGIN;
ALTER TABLE dialog ALTER COLUMN top_k TYPE INTEGER;
ALTER TABLE tenant_llm ALTER COLUMN api_key TYPE TEXT;
ALTER TABLE system_settings ALTER COLUMN value TYPE TEXT;
ALTER TABLE document ALTER COLUMN size TYPE BIGINT;
ALTER TABLE file ALTER COLUMN size TYPE BIGINT;
ALTER TABLE canvas_template ALTER COLUMN title TYPE TEXT;
ALTER TABLE canvas_template ALTER COLUMN description TYPE TEXT;
ALTER TABLE api_token ALTER COLUMN dialog_id TYPE VARCHAR(32);
ALTER TABLE api_token ALTER COLUMN dialog_id DROP NOT NULL;
COMMIT;
```

---

## Step 4：重启 ragflow_server 让模型层重新加载

虽然新列已经通过 SQL 加好，但 Peewee 的 model class 在内存里第一次失败后可能缓存了 schema 信息。保险起见重启一下。

```bash
# 容器内强杀 ragflow_server，supervisord 自动拉起
docker exec -it ragflow-server bash -c "pkill -9 -f ragflow_server && sleep 2 && while ! supervisorctl status ragflow_server | grep -q RUNNING; do sleep 1; done && supervisorctl status ragflow_server"
```

---

## Step 5：还原 common_service.py 调试代码（可选但推荐）

定位完成，把之前加的 `[DEBUG] get_by_id` 日志去掉，避免后续日志噪音。

文件：`api/db/services/common_service.py`，把 `get_by_id` 改回：

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

然后再跑一次 Step 4 的重启命令。

---

## Step 6：web UI 验证

浏览器退出登录 → 重新登录 → 创建知识库。

如果仍然报 `Tenant not found.`，把 Step 4 重启后到触发错误之间的完整日志贴出来：

```bash
docker exec -it ragflow-server bash -c \
  "tail -300 /ragflow/log/ragflow_server.log | grep -E 'DEBUG get_by_id|Tenant not found|EXCEPTION|Traceback'"
```
