# RAGFlow ES 客户端并发优化

## 背景

RAGFlow HA 部署中，检索并发升高时延迟显著增加，但 ES 节点资源利用率极低（<10%）。通过 ES 搜索线程池监控确认 `active=0, queue=0`，瓶颈在客户端侧而非 ES 服务端。

## 修改一：增大 elasticsearch-py 连接池

**文件**: `common/doc_store/es_conn_pool.py`  
**行号**: 55-61

elasticsearch-py 默认 `connections_per_node=10`，每个 HTTP 连接同时只能处理一个请求。50+ 并发检索时，请求在客户端连接池排队。

```python
# 修改前
self.es_conn = Elasticsearch(
    self.ES_CONFIG["hosts"].split(","),
    basic_auth=(...),
    verify_certs=False,
    timeout=600
)

# 修改后
self.es_conn = Elasticsearch(
    self.ES_CONFIG["hosts"].split(","),
    basic_auth=(...),
    verify_certs=False,
    timeout=600,
    connections_per_node=self.ES_CONFIG.get("connections_per_node", 50)
)
```

可通过 `ES` 配置中的 `connections_per_node` 字段覆盖默认值 50。

## 修改二：检索链路耗时埋点

**文件**: `rag/nlp/search.py`  
**方法**: `Dealer.search()` (line 74)

共修改 5 处，在检索入口加入三段计时：`emb`（embedding）、`es`（ES 搜索）、`post`（后处理）。

### 2.1 方法入口 — 初始化计时器 (line 80-82)

```python
# 修改前
    if highlight is None:
        highlight = False

# 修改后
    _t0 = time.time()
    _t_emb = 0.0
    _t_es = 0.0
    if highlight is None:
        highlight = False
```

### 2.2 embedding 完成后 — 记录 embedding 耗时 (line 128)

```python
# 修改前
                matchDense = await self.get_vector(qst, emb_mdl, topk, req.get("similarity", 0.1))
                q_vec = matchDense.embedding_data

# 修改后
                matchDense = await self.get_vector(qst, emb_mdl, topk, req.get("similarity", 0.1))
                _t_emb = time.time() - _t0
                q_vec = matchDense.embedding_data
```

### 2.3 ES 搜索完成后 — 记录 ES 耗时 (line 138)

```python
# 修改前
                res = await thread_pool_exec(self.dataStore.search, src, highlightFields, filters, matchExprs, orderBy, offset, limit,
                                            idx_names, kb_ids, rank_feature=rank_feature)
                total = self.dataStore.get_total(res)

# 修改后
                res = await thread_pool_exec(self.dataStore.search, src, highlightFields, filters, matchExprs, orderBy, offset, limit,
                                            idx_names, kb_ids, rank_feature=rank_feature)
                _t_es = time.time() - _t0 - _t_emb
                total = self.dataStore.get_total(res)
```

### 2.4 非 embedding 路径 — 同样记录 ES 耗时 (line 120-123)

```python
# 修改前
            if emb_mdl is None:
                matchExprs = [matchText]
                res = await thread_pool_exec(self.dataStore.search, src, highlightFields, filters, matchExprs, orderBy, offset, limit,
                                            idx_names, kb_ids, rank_feature=rank_feature)
                total = self.dataStore.get_total(res)

# 修改后
            if emb_mdl is None:
                matchExprs = [matchText]
                _t_pre = time.time() - _t0
                res = await thread_pool_exec(self.dataStore.search, src, highlightFields, filters, matchExprs, orderBy, offset, limit,
                                            idx_names, kb_ids, rank_feature=rank_feature)
                _t_es = time.time() - _t0 - _t_pre
                total = self.dataStore.get_total(res)
```

### 2.5 return 前 — 输出三段计时 (line 168-169)

```python
# 修改前
        ids = self.dataStore.get_doc_ids(res)
        keywords = list(kwds)
        highlight = self.dataStore.get_highlight(res, keywords, "content_with_weight")
        aggs = self.dataStore.get_aggregation(res, "docnm_kwd")
        return self.SearchResult(

# 修改后
        ids = self.dataStore.get_doc_ids(res)
        keywords = list(kwds)
        highlight = self.dataStore.get_highlight(res, keywords, "content_with_weight")
        aggs = self.dataStore.get_aggregation(res, "docnm_kwd")
        _t_post = time.time() - _t0 - _t_emb - _t_es
        logging.warning(f"[TIMING] total={time.time()-_t0:.3f}s emb={_t_emb:.3f}s es={_t_es:.3f}s post={_t_post:.3f}s")
        return self.SearchResult(
```

### 日志输出示例

```
[TIMING] total=3.215s emb=2.850s es=0.052s post=0.313s
[TIMING] total=0.847s emb=0.315s es=0.055s post=0.477s
```

## 部署方式

Docker 容器内热更新，无需 rebuild：

```bash
for c in ha-node1-web ha-node2-web; do
  docker cp /path/to/ragflow/rag/nlp/search.py $c:/ragflow/rag/nlp/search.py
  docker cp /path/to/ragflow/common/doc_store/es_conn_pool.py $c:/ragflow/common/doc_store/es_conn_pool.py
done
docker exec ha-node1-web pkill -f ragflow_server
docker exec ha-node2-web pkill -f ragflow_server
```

进程会自动重启（entrypoint.sh 中 `while true` 循环）。

## 观察方法

```bash
# 实时看 TIMING 日志
docker logs -f ha-node1-web 2>&1 | grep TIMING

# ES 搜索线程池吞吐
BEFORE=$(curl ... | jq '.nodes[].thread_pool.search.completed')
# 压测 5s
AFTER=$(curl ... | jq '.nodes[].thread_pool.search.completed')
echo "$(( (AFTER-BEFORE)/5 )) QPS"
```

## 调用链

```
API 请求
  └─ Dealer.search()          [rag/nlp/search.py:74]
       ├─ get_vector()         [line 127] → thread_pool_exec → embedding
       └─ dataStore.search()   [line 136] → thread_pool_exec → ES
              ↑ 共享 ThreadPoolExecutor（默认 128 workers）
```
