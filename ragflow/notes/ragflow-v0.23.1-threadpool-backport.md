# RAGFlow v0.23.1 并发性能修复 — 最小实现方案

## 问题

v0.23.1 的 `Dealer.search()` 是同步函数，在 Quart async 事件循环中直接调用，阻塞整个事件循环，导致并发请求串行化。

## 最小实现（6 个文件）

### 核心层（3 个文件）：添加 thread_pool_exec 基础设施 + 改造检索方法为异步

---

### 文件一：`common/misc_utils.py`

**新增** `thread_pool_exec()` 函数。在文件末尾 `pip_install_torch()` 之后追加。

```python
# ===== 新增 import（文件头部） =====
import asyncio
import functools
import os
from concurrent.futures import ThreadPoolExecutor

# ===== 新增函数（文件末尾） =====

@once
def _thread_pool_executor():
    max_workers_env = os.getenv("THREAD_POOL_MAX_WORKERS", "128")
    try:
        max_workers = int(max_workers_env)
    except ValueError:
        max_workers = 128
    if max_workers < 1:
        max_workers = 1
    return ThreadPoolExecutor(max_workers=max_workers)


async def thread_pool_exec(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    if kwargs:
        func = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(_thread_pool_executor(), func)
    return await loop.run_in_executor(_thread_pool_executor(), func, *args)
```

### 文件二：`rag/nlp/search.py`

**改动 A** — import 变更：

```python
# 删除
import asyncio

# 新增（放在其他 import 之后）
from common.misc_utils import thread_pool_exec
```

**改动 B** — `get_vector()`: `def` → `async def`，embedding 调用包裹为 `await thread_pool_exec()`：

```python
# 修改前 (line 53)
    def get_vector(self, txt, emb_mdl, topk=10, similarity=0.1):
        qv, _ = emb_mdl.encode_queries(txt)

# 修改后
    async def get_vector(self, txt, emb_mdl, topk=10, similarity=0.1):
        qv, _ = await thread_pool_exec(emb_mdl.encode_queries, txt)
```

**改动 C** — `search()`: `def` → `async def`，所有 `self.dataStore.search()` 包裹为 `await thread_pool_exec()`，`self.get_vector()` 前加 `await`：

```python
# 修改前 (line 75)
    def search(self, req, idx_names: str | list[str],

# 修改后
    async def search(self, req, idx_names: str | list[str],
```

非 embedding 路径（line 118-119）：
```python
# 修改前
                res = self.dataStore.search(src, highlightFields, filters, matchExprs, orderBy, offset, limit,
                                            idx_names, kb_ids, rank_feature=rank_feature)

# 修改后
                res = await thread_pool_exec(self.dataStore.search, src, highlightFields, filters, matchExprs,
                                            orderBy, offset, limit, idx_names, kb_ids, rank_feature=rank_feature)
```

embedding 路径 — get_vector（line 127）：
```python
# 修改前
                matchDense = self.get_vector(qst, emb_mdl, topk, req.get("similarity", 0.1))

# 修改后
                matchDense = await self.get_vector(qst, emb_mdl, topk, req.get("similarity", 0.1))
```

embedding 路径 — ES 搜索（line 131-132）：
```python
# 修改前
                res = self.dataStore.search(src, highlightFields, filters, matchExprs, orderBy, offset, limit,
                                            idx_names, kb_ids, rank_feature=rank_feature)

# 修改后
                res = await thread_pool_exec(self.dataStore.search, src, highlightFields, filters, matchExprs,
                                            orderBy, offset, limit, idx_names, kb_ids, rank_feature=rank_feature)
```

空结果重试 — doc_id 路径（line 136-138）：
```python
# 修改前
                        res = self.dataStore.search(src, [], filters, [], orderBy, offset, limit, idx_names, kb_ids)

# 修改后
                        res = await thread_pool_exec(self.dataStore.search, src, [], filters, [], orderBy, offset, limit,
                                                    idx_names, kb_ids)
```

空结果重试 — 低阈值路径（line 141-144）：
```python
# 修改前
                        res = self.dataStore.search(src, highlightFields, filters, [matchText, matchDense, fusionExpr],
                                                    orderBy, offset, limit, idx_names, kb_ids,
                                                    rank_feature=rank_feature)

# 修改后
                        res = await thread_pool_exec(self.dataStore.search, src, highlightFields, filters,
                                                    [matchText, matchDense, fusionExpr],
                                                    orderBy, offset, limit, idx_names, kb_ids,
                                                    rank_feature=rank_feature)
```

**改动 D** — `retrieval()`: `def` → `async def`，内部 `self.search()` 加 `await`：

```python
# 修改前 (line 363)
    def retrieval(

# 修改后
    async def retrieval(
```

search 调用（line 398）：
```python
# 修改前
        sres = self.search(req, [index_name(tid) for tid in tenant_ids], kb_ids, embd_mdl, highlight,

# 修改后
        sres = await self.search(req, [index_name(tid) for tid in tenant_ids], kb_ids, embd_mdl, highlight,
```

**改动 E** — `retrieval_by_toc()`: `def` → `async def`，`asyncio.run()` → `await`：
```python
# 修改前 (line 592)
    def retrieval_by_toc(self, query: str, chunks: list[dict], tenant_ids: list[str], chat_mdl, topn: int = 6):

# 修改后
    async def retrieval_by_toc(self, query: str, chunks: list[dict], tenant_ids: list[str], chat_mdl, topn: int = 6):
        from rag.prompts.generator import relevant_chunks_with_toc
```

```python
# 修改前 (line 617)
        ids = asyncio.run(relevant_chunks_with_toc(query, toc, chat_mdl, topn * 2))

# 修改后
        ids = await relevant_chunks_with_toc(query, toc, chat_mdl, topn * 2)
```

### 文件三：`api/apps/chunk_app.py`

4 处调用加 `await`。

**改动 A** — `list_chunk()` (line 64)，已在 `async def` 中，直接加 `await`：

```python
# 修改前
        sres = settings.retriever.search(query, search.index_name(tenant_id), kb_ids, highlight=["content_ltks"])

# 修改后
        sres = await settings.retriever.search(query, search.index_name(tenant_id), kb_ids, highlight=["content_ltks"])
```

**改动 B** — `retrieval_test()` (line 375)，已在 `async def` 中，加 `await`：

```python
# 修改前
        ranks = settings.retriever.retrieval(_question, embd_mdl, tenant_ids, kb_ids, page, size,
                               float(req.get("similarity_threshold", 0.0)),
                               float(req.get("vector_similarity_weight", 0.3)),
                               top,
                               local_doc_ids, rerank_mdl=rerank_mdl,
                                             highlight=req.get("highlight", False),
                               rank_feature=labels
                               )

# 修改后
        ranks = await settings.retriever.retrieval(_question, embd_mdl, tenant_ids, kb_ids, page, size,
                               float(req.get("similarity_threshold", 0.0)),
                               float(req.get("vector_similarity_weight", 0.3)),
                               top,
                               local_doc_ids, rerank_mdl=rerank_mdl,
                                             highlight=req.get("highlight", False),
                               rank_feature=labels
                               )
```

**改动 C** — `knowledge_graph()` (line 408)，`def` → `async def`，加 `await`：

```python
# 修改前
def knowledge_graph():

# 修改后
async def knowledge_graph():
```

```python
# 修改前 (line 418)
    sres = settings.retriever.search(req, search.index_name(tenant_id), kb_ids)

# 修改后
    sres = await settings.retriever.search(req, search.index_name(tenant_id), kb_ids)
```

**改动 D** — `kg_retriever.retrieval()` 调用 (line 384)，暂时注释掉：

```python
# 注释掉（KGSearch.retrieval 未同步修改，会报错）
#         if use_kg:
#             ck = settings.kg_retriever.retrieval(...)
#             if ck["content_with_weight"]:
#                 ranks["chunks"].insert(0, ck)
```

> **说明**：`KGSearch` 继承 `Dealer`，其 `retrieval()` 也需要改为 async，但内部调用了多个同步辅助方法（`query_rewrite`、`get_relevant_ents_by_keywords`、`_community_retrieval_`），改动链路长。最小验证跳过 KGSearch，专注核心检索链路。所有 SDK 文件中的 `kg_retriever.retrieval()` 调用均用同样方式注释。

---

### 调用层 B：`api/apps/sdk/doc.py`（SDK 检索接口）

**改动** — `retrieval_test()` (line 1561)，已在 `async def` 中，3 处加 `await` + 注释 kg_retriever：

```python
# 修改前 (line 1561)
        ranks = settings.retriever.retrieval(
            question, embd_mdl, tenant_ids, kb_ids, page, size,
            ...
        )
# 修改后
        ranks = await settings.retriever.retrieval(
            question, embd_mdl, tenant_ids, kb_ids, page, size,
            ...
        )
```

```python
# 修改前 (line 1578)
            cks = settings.retriever.retrieval_by_toc(question, ranks["chunks"], tenant_ids, chat_mdl, size)

# 修改后
            cks = await settings.retriever.retrieval_by_toc(question, ranks["chunks"], tenant_ids, chat_mdl, size)
```

```python
# 修改前 (line 1582-1584)
        if use_kg:
            ck = settings.kg_retriever.retrieval(...)
            if ck["content_with_weight"]:
                ranks["chunks"].insert(0, ck)

# 修改后 — 注释掉
        # NOTE: kg_retriever.retrieval skipped in minimal backport (KGSearch not yet async)
        # if use_kg:
        #     ck = settings.kg_retriever.retrieval(...)
        #     if ck["content_with_weight"]:
        #         ranks["chunks"].insert(0, ck)
```

### 调用层 C：`api/apps/sdk/dify_retrieval.py`（Dify 兼容检索接口）

**改动** — `retrieval()` (line 138)，已在 `async def` 中，1 处加 `await` + 注释 kg_retriever：

```python
# 修改前 (line 138)
        ranks = settings.retriever.retrieval(
            question, embd_mdl, kb.tenant_id, [kb_id], ...

# 修改后
        ranks = await settings.retriever.retrieval(
            question, embd_mdl, kb.tenant_id, [kb_id], ...
```

同样注释掉 kg_retriever 块（lines 152-160）。

### 调用层 D：`api/apps/sdk/session.py`（会话检索测试接口）

**改动** — `retrieval_test_embedded()` (line 1114)，已在 `async def` 中，1 处加 `await` + 注释 kg_retriever：

```python
# 修改前 (line 1114)
        ranks = settings.retriever.retrieval(
            _question, embd_mdl, tenant_ids, kb_ids, page, size, ...

# 修改后
        ranks = await settings.retriever.retrieval(
            _question, embd_mdl, tenant_ids, kb_ids, page, size, ...
```

同样注释掉 kg_retriever 块（lines 1118-1122）。

---

## 部署

```bash
for c in ha-node1-web ha-node2-web; do
  docker cp common/misc_utils.py $c:/ragflow/common/misc_utils.py
  docker cp rag/nlp/search.py $c:/ragflow/rag/nlp/search.py
  docker cp api/apps/chunk_app.py $c:/ragflow/api/apps/chunk_app.py
  docker cp api/apps/sdk/doc.py $c:/ragflow/api/apps/sdk/doc.py
  docker cp api/apps/sdk/dify_retrieval.py $c:/ragflow/api/apps/sdk/dify_retrieval.py
  docker cp api/apps/sdk/session.py $c:/ragflow/api/apps/sdk/session.py
done
docker exec ha-node1-web pkill -f ragflow_server
docker exec ha-node2-web pkill -f ragflow_server
```

## 验证

```bash
# 观察 TIMING 日志
docker logs -f ha-node1-web 2>&1 | grep TIMING

# 压测并发检索
# 预期：50 并发平均延迟从数秒降至 <2s，ES active 可观测到 >0
```

## 不改动的范围

以下调用点在最小实现中**暂不修改**（不在 `async def` 中，改为 async 会级联修改更多文件）：

| 文件 | 调用 | 所在函数 |
|------|------|---------|
| `api/apps/sdk/doc.py:1084` | `retriever.search()` | `def list_chunks()` sync |
| `api/apps/sdk/dataset.py:500` | `retriever.search()` | `def knowledge_graph()` sync |
| `api/apps/kb_app.py:391` | `retriever.search()` | `def knowledge_graph()` sync |
| `graphrag/search.py` | `KGSearch.retrieval()` 内部 | 继承 Dealer，链路复杂 |
| `api/db/services/dialog_service.py` | 对话检索 | 非当前测试范围 |
| `agent/tools/retrieval.py` | Agent 检索 | 非当前测试范围 |
| `api/apps/llm_app.py` | `asyncio.to_thread()` | LLM 测试接口，非检索路径 |
