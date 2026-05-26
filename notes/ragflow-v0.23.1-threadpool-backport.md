# RAGFlow v0.23.1 并发性能修复 — thread_pool_exec 回移植方案

## 问题根因

v0.23.1 的 `Dealer.search()` 和 `Dealer.retrieval()` 是**同步阻塞函数**，直接在 Quart 的 async 事件循环中调用。同步阻塞代码在事件循环中执行时会阻塞整个事件循环，导致并发请求被串行化。

```
50 并发 → 第1个请求进入 Dealer.search() 阻塞 0.4s
       → 事件循环被阻塞，其余 49 个请求全部排队
       → 50 个请求串行完成 = 50 × 0.4s ≈ 20s
```

这就是为什么：
- 单次 ES 搜索只需 0.3-0.4s
- 50 并发时平均延迟却有数秒
- ES 线程池 `active=0`（请求被串行化，从未并发到达 ES）

**修复思路**：将同步阻塞调用通过 `ThreadPoolExecutor` 卸到线程池中执行，释放事件循环去处理其他请求。这个修复在 commit `927db0b37` (#12716) 中引入。

## 需要修改的文件清单

共涉及 **~15 个文件**，按修改类型分为三层：

---

### 第一层：基础设施 — `common/misc_utils.py`

**新增** `thread_pool_exec()` 函数 + `_thread_pool_executor()` 单例。

```python
# ===== 新增 import =====
import asyncio
import functools
import os
from concurrent.futures import ThreadPoolExecutor

# ===== 新增函数（放在文件末尾，pip_install_torch 之后）=====

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

---

### 第二层：核心 — `rag/nlp/search.py`

#### 2.1 import 变更

```python
# 删除
import asyncio

# 新增
from common.misc_utils import thread_pool_exec
```

#### 2.2 `get_vector()` — 同步 → 异步

```python
# 修改前 (line 53)
    def get_vector(self, txt, emb_mdl, topk=10, similarity=0.1):
        qv, _ = emb_mdl.encode_queries(txt)

# 修改后
    async def get_vector(self, txt, emb_mdl, topk=10, similarity=0.1):
        qv, _ = await thread_pool_exec(emb_mdl.encode_queries, txt)
```

#### 2.3 `search()` — 同步 → 异步（5 处 thread_pool_exec 包裹）

```python
# 修改前 (line 75)
    def search(self, req, idx_names: str | list[str],

# 修改后
    async def search(self, req, idx_names: str | list[str],
```

非 embedding 路径（line 118-119 in v0.23.1）：
```python
# 修改前
                res = self.dataStore.search(src, highlightFields, filters, matchExprs, orderBy, offset, limit,
                                            idx_names, kb_ids, rank_feature=rank_feature)

# 修改后
                res = await thread_pool_exec(self.dataStore.search, src, highlightFields, filters, matchExprs,
                                            orderBy, offset, limit, idx_names, kb_ids, rank_feature=rank_feature)
```

embedding 路径 — get_vector 调用（line 127 in v0.23.1）：
```python
# 修改前
                matchDense = self.get_vector(qst, emb_mdl, topk, req.get("similarity", 0.1))

# 修改后
                matchDense = await self.get_vector(qst, emb_mdl, topk, req.get("similarity", 0.1))
```

embedding 路径 — ES 搜索（line 131-132 in v0.23.1）：
```python
# 修改前
                res = self.dataStore.search(src, highlightFields, filters, matchExprs, orderBy, offset, limit,
                                            idx_names, kb_ids, rank_feature=rank_feature)

# 修改后
                res = await thread_pool_exec(self.dataStore.search, src, highlightFields, filters, matchExprs,
                                            orderBy, offset, limit, idx_names, kb_ids, rank_feature=rank_feature)
```

空结果重试 — doc_id 路径（line 136-138 in v0.23.1）：
```python
# 修改前
                        res = self.dataStore.search(src, [], filters, [], orderBy, offset, limit, idx_names, kb_ids)

# 修改后
                        res = await thread_pool_exec(self.dataStore.search, src, [], filters, [], orderBy, offset, limit,
                                                    idx_names, kb_ids)
```

空结果重试 — 低阈值路径（line 141-144 in v0.23.1）：
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

#### 2.4 `retrieval()` — 同步 → 异步（1 处 await）

```python
# 修改前 (line 363)
    def retrieval(

# 修改后
    async def retrieval(
```

search 调用（line 398 in v0.23.1）：
```python
# 修改前
        sres = self.search(req, [index_name(tid) for tid in tenant_ids], kb_ids, embd_mdl, highlight,

# 修改后
        sres = await self.search(req, [index_name(tid) for tid in tenant_ids], kb_ids, embd_mdl, highlight,
```

#### 2.5 `retrieval_by_toc()` — 同步 → 异步（1 处 await）

```python
# 修改前 (line 592)
    def retrieval_by_toc(self, query: str, chunks: list[dict], tenant_ids: list[str], chat_mdl, topn: int = 6):

# 修改后
    async def retrieval_by_toc(self, query: str, chunks: list[dict], tenant_ids: list[str], chat_mdl, topn: int = 6):
        from rag.prompts.generator import relevant_chunks_with_toc  # 移到方法内避免循环引用
```

asyncio.run → await（line 617 in v0.23.1）：
```python
# 修改前
        ids = asyncio.run(relevant_chunks_with_toc(query, toc, chat_mdl, topn * 2))

# 修改后
        ids = await relevant_chunks_with_toc(query, toc, chat_mdl, topn * 2)
```

#### 2.6 不需要改的方法

| 方法 | 原因 |
|------|------|
| `retrieval_by_children()` | 同步方法，调用者不 await，不阻塞事件循环 |
| `all_tags()`, `all_tags_in_portion()`, `tag_query()`, `tag_content()` | 同步查询方法，不在 HTTP 请求路径上 |
| `chunk_list()`, `sql_retrieval()` | 同步生成器方法 |

---

### 第三层：调用方 — 添加 `await`

每个调用方需要以下改动：
1. 如果当前函数是 `async def`：只需在调用前加 `await`
2. 如果当前函数是 `def`：需要先改为 `async def`，再加 `await`
3. 如果已经是 `async def` 且已有 `await`（如 `llm_app.py`）：将 `asyncio.to_thread()` 替换为 `thread_pool_exec()`

#### 文件 A：`api/apps/chunk_app.py`（4 处）

| 行号 | 当前调用 | 需要改动 |
|------|---------|---------|
| 64 | `sres = settings.retriever.search(...)` | 加 `await`，已在 `async def list_chunk()` 中 |
| 375 | `ranks = settings.retriever.retrieval(...)` | 加 `await`，已在 `async def retrieval_test()` 中 |
| 384 | `ck = settings.kg_retriever.retrieval(...)` | 加 `await` |
| 418 | `sres = settings.retriever.search(...)` | 需先改 `def knowledge_graph()` → `async def`，再加 `await` |

#### 文件 B：`api/apps/kb_app.py`（1 处）

| 行号 | 当前调用 | 需要改动 |
|------|---------|---------|
| 391 | `sres = settings.retriever.search(...)` | 加 `await`，需确认所在函数是否 async |

额外：`asyncio.to_thread()` 替换为 `thread_pool_exec()`（3 处，lines 133, 142, 293）。

#### 文件 C：`api/apps/sdk/doc.py`（4 处）

| 行号 | 当前调用 | 需要改动 |
|------|---------|---------|
| 1084 | `sres = settings.retriever.search(...)` | 加 `await` |
| 1561 | `ranks = settings.retriever.retrieval(...)` | 加 `await` |
| 1578 | `cks = settings.retriever.retrieval_by_toc(...)` | 加 `await` |
| 1582 | `ck = settings.kg_retriever.retrieval(...)` | 加 `await` |

#### 文件 D：`api/apps/sdk/dataset.py`（1 处）

| 行号 | 当前调用 | 需要改动 |
|------|---------|---------|
| 500 | `sres = settings.retriever.search(...)` | 加 `await`，需确认所在函数是否 async |

#### 文件 E：`api/apps/sdk/dify_retrieval.py`（2 处）

| 行号 | 当前调用 | 需要改动 |
|------|---------|---------|
| 138 | `ranks = settings.retriever.retrieval(...)` | 加 `await` |
| 153 | `ck = settings.kg_retriever.retrieval(...)` | 加 `await` |

#### 文件 F：`api/apps/sdk/session.py`（2 处）

| 行号 | 当前调用 | 需要改动 |
|------|---------|---------|
| 1114 | `ranks = settings.retriever.retrieval(...)` | 加 `await` |
| 1119 | `ck = settings.kg_retriever.retrieval(...)` | 加 `await` |

#### 文件 G：`api/db/services/dialog_service.py`（2 处）

| 行号 | 当前调用 | 需要改动 |
|------|---------|---------|
| 424 | `ck = settings.kg_retriever.retrieval(...)` | 加 `await` |
| 828 | `ranks = settings.retriever.retrieval(...)` | 加 `await`，需确认所在函数是否 async |

#### 文件 H：`agent/tools/retrieval.py`（4 处）

| 行号 | 当前调用 | 需要改动 |
|------|---------|---------|
| 177 | `kbinfos = settings.retriever.retrieval(...)` | 加 `await` |
| 196 | `cks = settings.retriever.retrieval_by_toc(...)` | 加 `await` |
| 205 | `ck = settings.kg_retriever.retrieval(...)` | 加 `await` |
| 218 | `ck = settings.kg_retriever.retrieval(...)` | 加 `await` |

#### 文件 I：`graphrag/utils.py`（4 处）

| 行号 | 当前调用 | 需要改动 |
|------|---------|---------|
| 340 | `es_res = settings.retriever.search(...)` | 加 `await` |
| 408 | 传 `settings.retriever.search` 作为回调 | 不需改（传引用，不调用） |
| 424 | `settings.retriever.search` | 不需改（传引用） |
| 630 | `es_res = settings.retriever.search(...)` | 加 `await` |

#### 文件 J：其他

| 文件 | 内容 |
|------|------|
| `rag/benchmark.py:55` | `asyncio.run(settings.retriever.retrieval(...))` — 改用 `asyncio.run()` 包裹 async 方法即可 |
| `api/apps/llm_app.py` | 多处 `asyncio.to_thread()` 替换为 `thread_pool_exec()` |
| `api/apps/canvas_app.py` | `asyncio.to_thread()` 替换为 `thread_pool_exec()` |

---

## 建议的验证步骤

### 最小验证集（证明方案可行）

只需改 3 个文件，覆盖检索 API 的核心路径：

1. **`common/misc_utils.py`** — 新增 `thread_pool_exec()`
2. **`rag/nlp/search.py`** — `search()`, `get_vector()`, `retrieval()` 改为 async
3. **`api/apps/chunk_app.py`** — 4 处调用加 `await`

改完后部署到容器，压测检索 API，对比修改前后的并发延迟。

### 完整修复

按上述表格逐文件修改，所有 `asyncio.to_thread()` 替换为 `thread_pool_exec()`。

### 验证方法

```bash
# 部署
for c in ha-node1-web ha-node2-web; do
  docker cp common/misc_utils.py $c:/ragflow/common/misc_utils.py
  docker cp rag/nlp/search.py $c:/ragflow/rag/nlp/search.py
  docker cp api/apps/chunk_app.py $c:/ragflow/api/apps/chunk_app.py
done
docker exec ha-node1-web pkill -f ragflow_server
docker exec ha-node2-web pkill -f ragflow_server

# 压测观察
docker logs -f ha-node1-web 2>&1 | grep -E "TIMING|THREADPOOL"
```

预期结果：
- TIMING `es` 保持 0.3-0.4s
- 50 并发下平均延迟显著下降（从数秒降至 <2s）
- ES `active` 可观测到 >0
