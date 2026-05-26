# Elasticsearch 资源利用率低的排查方法

## 场景

RAGFlow 检索并发升高时延迟显著增加，但 ES 节点 CPU/内存利用率不到 10%，资源"起不来"。瓶颈大概率在客户端侧，而非 ES 服务端。

## 排查层级

### 第一层：确认 ES 是否收到了足够多的请求

排查 ES 搜索线程池状态——看是否有请求堆积或排队。

```bash
# 查看搜索线程池状态（active=当前执行数, queue=排队数, rejected=拒绝数）
curl -s "http://localhost:11200/_nodes/stats/thread_pool?pretty" \
  -u elastic:ha_test_es_pwd | \
  jq '.nodes[].thread_pool.search'
```

**判断标准**：
- `active` 和 `queue` 长期为 0 → 请求根本没大量到达 ES，瓶颈在客户端
- `rejected` > 0 → ES 线程池过载，需要调大或扩容

**重要：`active` 的含义与误区**

`active` 是**瞬时快照**，不是平均值。它表示采样那一刻正在线程池中执行的搜索任务数。

| 场景 | active 表现 | 含义 |
|------|------------|------|
| 每 2s 发一个搜索，ES 100ms 返回 | active 几乎永远为 0 | 请求间隔远大于执行时间，采样无法捕捉 |
| 20 并发搜索同时到，ES 100ms 返回 | active 能看到 ≥5 | 短时间窗口内有重叠 |
| 20 并发搜索同时到，但连接池只允许 10 并发 | active 可能为 0-2 | 客户端连接池把并发度摊平了 |
| 检索耗时 5s，但 ES 搜索只占 100ms | active 几乎永远为 0 | 99% 时间花在 embedding/rerank 等非 ES 阶段 |

**压测时 `active=0` 但检索耗时数秒，说明两件事同时发生：**

1. **ES 搜索在端到端检索中的占比极低** —— 生成 query embedding（1-3s）+ rerank（0.5-2s）占据绝大部分时间，ES 搜索本身只有 50-200ms
2. **请求的 ES 搜索阶段在时间轴上没有重叠** —— 要么是客户端连接池太小（10），要么是上游 embedding 阶段已经串行化（embedding 模型一次只处理一个请求），导致 ES 搜索阶段被自然错开

### 第二层：确认 ES 单次查询的实际耗时

开启 ES 慢查询日志，记录所有超过 50ms 的查询。

```bash
# 开启慢查询日志
curl -XPUT "http://localhost:11200/_cluster/settings" \
  -u elastic:ha_test_es_pwd \
  -H "Content-Type: application/json" -d '{
  "transient": {
    "search.default_search_timeout": "30s",
    "index.search.slowlog.threshold.query.info": "100ms",
    "index.search.slowlog.threshold.query.debug": "50ms",
    "index.search.slowlog.level": "info"
  }
}'

# 压测后查看慢日志
docker exec ha-es01 cat /usr/share/elasticsearch/logs/elasticsearch_index_search_slowlog.log
```

**判断标准**：
- 慢日志显示单次查询 50-200ms，但端到端 20s+ → 99% 时间在客户端排队
- 慢日志显示单次查询 >1s → ES 自身有问题，继续排查

### 第三层：确认客户端连接池是否饱和

elasticsearch-py 默认每节点最多 10 个连接。如果并发超过此数，请求在客户端排队。

```bash
# 看 ES 侧当前的活跃 HTTP 连接数
curl -s "http://localhost:11200/_nodes/stats/http?pretty" \
  -u elastic:ha_test_es_pwd | \
  jq '.nodes[].http'
```

**判断标准**：
- `current_open` 接近 10，但并发请求 >10 → 客户端连接池饱和
- `total_opened` 快速增长 → 连接频繁创建/销毁，可能连接泄漏

### 第四层：索引层面排查

```bash
# 查看索引大小（判断 OS 页面缓存是否足够）
curl -s "http://localhost:11200/_cat/indices?v&h=index,pri.store.size,docs.count" \
  -u elastic:ha_test_es_pwd

# 查看索引设置（分片数、副本数、刷新间隔）
curl -s "http://localhost:11200/_settings?pretty" \
  -u elastic:ha_test_es_pwd | \
  jq '.[].settings.index | {shards, replicas, refresh_interval}'
```

### 第五层：ES 容器资源使用

```bash
# 实时查看 ES 容器的 CPU/内存使用
docker stats ha-es01

# 查看 ES JVM 堆使用情况
curl -s "http://localhost:11200/_nodes/stats/jvm?pretty" \
  -u elastic:ha_test_es_pwd | \
  jq '.nodes[].jvm.mem | {
    heap_used_pct: (.heap_used_percent),
    heap_max_gb: (.heap_max_in_bytes / 1073741824),
    heap_used_gb: (.heap_used_in_bytes / 1073741824)
  }'

# 查看 OS 内存（mmap 相关）
curl -s "http://localhost:11200/_nodes/stats/os?pretty" \
  -u elastic:ha_test_es_pwd | \
  jq '.nodes[].os.mem'
```

### 第六层：在 RAGFlow 客户端侧加监控

在 `rag/utils/es_conn.py` 的 `search()` 方法中加耗时记录，与 ES 慢日志对比。

```python
import time

# search() 方法开头
_start = time.time()

# ... 原有搜索逻辑 ...

# search() 方法结尾（result 返回前）
_elapsed = time.time() - _start
logging.warning(f"ES search actual time: {_elapsed:.3f}s, index={index_name}")
```

## 最可能的瓶颈（按概率排序）

| 瓶颈位置 | 症状 | 方案 |
|----------|------|------|
| elasticsearch-py 连接池耗尽（默认 maxsize=10） | ES 资源空闲，`active=0`，客户端线程阻塞在连接池 | 增大 `connections_per_node`（见下方代码修改） |
| Embedding 模型串行处理 | ES `active=0`，但 embedding 调用耗时长 | 多实例 embedding 模型或增加并发调用 |
| Quart 单 worker 串行处理 | 并发请求在 Quart 层排队 | 多 worker 部署或增加 API 节点数量 |
| Global ThreadPoolExecutor 饱和（默认 128） | 大量线程等待 ES 响应 | 调大 `THREAD_POOL_MAX_WORKERS` 环境变量 |
| ES 搜索线程池不足 | ES `rejected` > 0 | 调大 ES `thread_pool.search.size` |
| OS 页面缓存不足，频繁磁盘 I/O | ES 磁盘 IOPS 高，CPU wait 高 | 增加容器内存或减小索引大小 |
| HNSW 向量图过大，num_candidates 高 | KNN 查询自身耗时 >1s | 调低 `num_candidates` 上限 |

## 代码修改：增大 ES 客户端连接池

`common/doc_store/es_conn_pool.py`，在 `Elasticsearch()` 初始化时增加 `connections_per_node` 参数：

```python
# 修改前（默认 maxsize=10）
self.es_conn = Elasticsearch(
    self.ES_CONFIG["hosts"].split(","),
    basic_auth=(...),
    verify_certs=False,
    timeout=600
)

# 修改后（默认 maxsize=50，可通过 ES 配置覆盖）
self.es_conn = Elasticsearch(
    self.ES_CONFIG["hosts"].split(","),
    basic_auth=(...),
    verify_certs=False,
    timeout=600,
    connections_per_node=self.ES_CONFIG.get("connections_per_node", 50)
)
```

对于 Docker 部署的 HA 环境，需要在 docker-compose 中增加 volume mount 将修改后的文件覆盖到容器：

```yaml
volumes:
  - ../../common/doc_store/es_conn_pool.py:/ragflow/common/doc_store/es_conn_pool.py
```

修改后重启容器，压测时观察 ES `active` 是否从 0 变为正数。

## ES 性能优化速查

```bash
# 1. 调整 JVM 堆（docker-compose 中设置）
#   ES_JAVA_OPTS: "-Xms2g -Xmx2g"   # 不超过容器内存的 50%

# 2. 单节点建议分片数设为 1（conf/mapping.json）
#   "number_of_shards": 1

# 3. 关闭精确 hit 计数（es_conn.py 中改为）
#   "track_total_hits": 10000

# 4. 系统参数
#   sysctl -w vm.max_map_count=262144
#   ulimit -n 65536

# 5. 关闭 swap
#   bootstrap.memory_lock: true  （同时 memlock ulimit 设为 -1）
```
