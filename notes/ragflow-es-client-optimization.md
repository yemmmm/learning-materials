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

在检索入口方法中加入三段计时：
- `emb`: embedding 生成耗时
- `es`: ES 搜索耗时（不含 embedding）
- `post`: 结果后处理耗时（highlight、aggregation 等）

```python
# 方法入口新增
_t0 = time.time()
_t_emb = 0.0
_t_es = 0.0

# embedding 完成后
_t_emb = time.time() - _t0

# ES 搜索完成后
_t_es = time.time() - _t0 - _t_emb

# return 前
_t_post = time.time() - _t0 - _t_emb - _t_es
logging.warning(f"[TIMING] total={time.time()-_t0:.3f}s emb={_t_emb:.3f}s es={_t_es:.3f}s post={_t_post:.3f}s")
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
