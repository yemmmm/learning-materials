# RAGFlow 检索 API 性能压测工具集

对 RAGFlow 检索 API 进行全维度性能测试，支持检索压测、Embedding 模型测试、Docker 资源监控、检索管道耗时分析和交互式配置。

## 目录

- [环境准备](#环境准备)
- [快速开始](#快速开始)
- [获取 API 凭证](#获取-api-凭证)
- [工具详解](#工具详解)
  - [run_bench.py — 交互式主控](#run_benchpy--交互式主控)
  - [bench_retrieval.py — 检索压测](#bench_retrievalpy--检索压测)
  - [bench_embedding.py — Embedding 测试](#bench_embeddingpy--embedding-测试)
  - [monitor_resources.sh — 资源监控](#monitor_resourcessh--资源监控)
  - [plot_monitor.py — 图表生成](#plot_monitorpy--图表生成)
  - [analyze_logs.py — 日志分析](#analyze_logspy--日志分析)
- [配置文件格式](#配置文件格式)
- [多节点部署支持](#多节点部署支持)
- [结果解读](#结果解读)
- [常见问题](#常见问题)

---

## 环境准备

### 前提条件

- Python 3.10+
- 运行中的 RAGFlow 服务（单节点或 HA 集群均可）
- （可选）Docker — 资源监控和日志分析需要访问容器的 `docker` 命令

### 安装依赖

```bash
# 进入项目目录
cd retrieval-bench

# 方式一：使用 uv（推荐）
uv sync
# 或只装需要的包
uv pip install httpx pandas matplotlib numpy

# 方式二：使用 pip
pip install httpx pandas matplotlib numpy
```

---

## 快速开始

### 一键执行（推荐）

```bash
python run_bench.py
```

首次运行会引导你配置所有参数，之后会记住配置。这是最快的上手方式。

### 单工具快速验证

如果只想快速验证检索接口是否正常：

```bash
python bench_retrieval.py \
    --base-url http://<RAGFlow地址>:<端口> \
    --api-key <你的API Key> \
    --kb <知识库ID> --query "测试查询" \
    --concurrency 2 --duration 5
```

---

## 获取 API 凭证

压测需要两个信息：**RAGFlow 服务地址**和 **API Key**。知识库 ID 可从数据库或 Web UI 获取。

### 方法一：从 Web UI 获取

1. 浏览器打开 RAGFlow 地址（如 `http://<服务器IP>:18080`）
2. 登录后进入 **用户设置 → API** 页面
3. 复制 API Key（格式：`ragflow-xxxx`）
4. 数据集页面可以看到知识库列表，URL 中包含知识库 ID

### 方法二：从数据库查询

如果 MySQL 可访问，直接查询：

```sql
-- 获取 API Token
SELECT token FROM api_token LIMIT 1;

-- 获取知识库列表
SELECT id, name FROM knowledgebase;
```

MySQL 连接信息见 RAGFlow 部署配置中的 `common.env` 或 `docker/.env`。

### 方法三：通过容器内部查询

```bash
# 获取 API Token
docker exec <容器名> python -c "
import pymysql
conn = pymysql.connect(host='host.docker.internal', port=<MySQL端口>,
                       user='root', password='<密码>', database='rag_flow')
cur = conn.cursor()
cur.execute('SELECT token FROM api_token LIMIT 1')
print(cur.fetchone()[0])
conn.close()
"

# 获取知识库列表
docker exec <容器名> python -c "
import pymysql
conn = pymysql.connect(host='host.docker.internal', port=<MySQL端口>,
                       user='root', password='<密码>', database='rag_flow')
cur = conn.cursor()
cur.execute('SELECT id, name FROM knowledgebase')
for row in cur.fetchall():
    print(row)
conn.close()
"
```

### 验证凭证

```bash
curl -X POST http://<RAGFlow地址>/api/v1/retrieval \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <API Key>" \
  -d '{"dataset_ids":["<知识库ID>"],"question":"测试"}'
```

如果返回 `"code":109` 表示 API Key 无效，返回 `"code":0` 表示正常。

---

## 工具详解

### run_bench.py — 交互式主控

编排所有测试阶段的入口脚本。

```bash
# 交互式执行
python run_bench.py

# 使用已有配置文件
python run_bench.py --config bench_config.json

# 跳过某些阶段
python run_bench.py --skip-retrieval     # 跳过检索压测
python run_bench.py --skip-embedding     # 跳过 Embedding 测试
python run_bench.py --skip-monitor       # 跳过资源监控
python run_bench.py --skip-logs          # 跳过日志分析

# 查看帮助
python run_bench.py --help
```

**执行流程：**

1. 加载/配置参数（交互式）
2. 启动资源监控（后台，如果启用）
3. 执行检索压测
4. 执行 Embedding 测试（如果启用）
5. 等待监控完成
6. 执行日志分析（如果启用）
7. 生成资源图表

**交互配置包含 5 个部分：**

| 步骤 | 内容 | 关键参数 |
|------|------|---------|
| API 服务 | RAGFlow 地址和 API Key | `base_url`, `api_key` |
| 知识库 | 可配置多个 KB-Query 对 | `kb_queries` |
| 检索压测 | 并发数、持续时间、检索参数 | `concurrency`, `duration`, `top_k` |
| Embedding | 是否启用、API 地址、模型名 | `enabled`, `api_url`, `model` |
| 监控 & 日志 | 监控间隔、容器名、日志来源 | `interval`, `containers` |

---

### bench_retrieval.py — 检索压测

对 `/api/v1/retrieval` 接口进行并发压力测试。

```bash
python bench_retrieval.py \
    --base-url http://localhost:18080 \
    --api-key ragflow-xxxx \
    --kb <知识库ID1> --query "查询文本1" \
    --kb <知识库ID2> --query "查询文本2" \
    --concurrency 10 --duration 30 \
    --output-json results.json
```

**参数说明：**

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--base-url` | 是 | — | RAGFlow 服务地址 |
| `--api-key` | 是 | — | RAGFlow API Key |
| `--kb` | 是 | — | 知识库 ID（可多次指定） |
| `--query` | 是 | — | 对应的查询文本（与 --kb 一一对应） |
| `--concurrency` | 否 | 10 | 并发连接数 |
| `--duration` | 否 | 30 | 压测持续时间（秒） |
| `--top-k` | 否 | 1024 | 返回的最大 chunk 数 |
| `--similarity-threshold` | 否 | 0.2 | 相似度阈值 |
| `--vector-similarity-weight` | 否 | 0.3 | 向量相似度权重 |
| `--no-verify-ssl` | 否 | — | 跳过 SSL 证书验证 |
| `--output-json` | 否 | — | 保存 JSON 结果到文件 |
| `--config` | 否 | — | 从配置文件加载参数 |

**多知识库轮询：**

指定多个 `--kb` / `--query` 对时，每个并发 worker 按轮询方式选择 KB，模拟真实的多知识库混合负载：

```bash
python bench_retrieval.py \
    --base-url http://localhost:18080 \
    --api-key ragflow-xxxx \
    --kb kb_001 --query "机器学习" \
    --kb kb_002 --query "数据库优化" \
    --kb kb_003 --query "网络架构" \
    --concurrency 20 --duration 60
```

**输出报告示例：**

```
============================================================
  RAGFlow Retrieval 压测报告
============================================================

  目标:        http://localhost:18080/api/v1/retrieval
  知识库:      kb_001 (机器学习), kb_002 (数据库优化)
  并发数:      10
  持续时间:    30.0s

  --- 请求统计 ---
  总请求数:    342
  成功:        340
  失败:        2
  成功率:      99.4%
  QPS:         11.40

  --- 延迟统计 (秒) ---
  最小:        0.245
  最大:        4.521
  平均:        0.873
  中位数:      0.681
  标准差:      0.542
  P95:         2.138
  P99:         3.892

  --- 错误分布 ---
  ConnectError: Connection refused: 2
============================================================
```

---

### bench_embedding.py — Embedding 测试

测试 Embedding 模型的并发处理能力。支持 OpenAI 兼容 API 和 RAGFlow 内部格式。

```bash
# OpenAI 兼容格式
python bench_embedding.py \
    --api-url https://api.openai.com/v1/embeddings \
    --api-key sk-xxxx \
    --model text-embedding-ada-002 \
    --concurrency 5 --count 20

# RAGFlow 内部格式
python bench_embedding.py \
    --api-url http://localhost:18080/api/v1/embeddings \
    --api-key ragflow-xxxx \
    --model bge-large-zh-v1.5 \
    --api-format ragflow \
    --concurrency 3 --count 10
```

**参数说明：**

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--api-url` | 是 | — | Embedding API 完整地址 |
| `--api-key` | 否 | — | API Key（部分服务可选） |
| `--model` | 否 | text-embedding-ada-002 | 模型名称 |
| `--input` | 否 | 测试文本 | 测试输入文本 |
| `--concurrency` | 否 | 5 | 并发数（建议 ≤10） |
| `--count` | 否 | 20 | 总请求数（建议 ≤50） |
| `--api-format` | 否 | openai | API 格式：`openai` 或 `ragflow` |
| `--no-verify-ssl` | 否 | — | 跳过 SSL 证书验证 |
| `--output-json` | 否 | — | 保存 JSON 结果到文件 |

**安全提示：**

- 并发 > 20 或请求数 > 100 时会显示警告
- 短时间大量请求可能触发 API 风控，建议从小并发开始
- 使用 `--count 50` 以内的值通常比较安全

**并发分析：**

报告会对比前一半和后一半请求的平均延迟，如果延迟增长倍数 > 1.5x，说明存在并发排队现象。

---

### monitor_resources.sh — 资源监控

后台采集 Docker 容器和服务器资源指标，输出 CSV 文件。

```bash
# 自动检测所有 ha-* 容器，默认每 5 秒采样，持续 300 秒
./monitor_resources.sh

# 自定义参数
./monitor_resources.sh -i 2 -d 120 -o ./data

# 指定监控特定容器
./monitor_resources.sh -c "ha-node1-web ha-node1-worker ha-node2-web" -i 2 -d 120
```

**参数说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-i` | 5 | 采样间隔（秒） |
| `-d` | 300 | 监控总时长（秒） |
| `-o` | . | CSV 输出目录 |
| `-c` | 自动检测 | 监控的容器名称（空格分隔） |
| `-h` | — | 显示帮助 |

**采集指标：**

| CSV 文件 | 采集指标 |
|----------|---------|
| `container_stats_*.csv` | CPU%、内存使用(MB)、内存限制(MB)、内存%、网络入/出(KB)、磁盘读/写(KB) |
| `server_stats_*.csv` | CPU%、内存使用(GB)、内存总量(GB)、负载(1m/5m/15m)、磁盘使用(GB) |

**典型用法——配合压测：**

```bash
# 终端 1：启动监控（时长覆盖压测全程 + 缓冲）
./monitor_resources.sh -i 2 -d 180 -o ./bench-output &

# 终端 2：执行压测
python bench_retrieval.py --base-url http://localhost:18080 --api-key ragflow-xxx \
    --kb <KB_ID> --query "test" --concurrency 50 --duration 120

# 压测结束后：生成图表
python plot_monitor.py -d ./bench-output -o ./bench-output
```

---

### plot_monitor.py — 图表生成

读取监控 CSV 文件，生成可视化的资源使用图表。

```bash
# 读取当前目录下的 CSV 并生成图表
python plot_monitor.py

# 指定 CSV 目录和输出目录
python plot_monitor.py -d ./bench-data -o ./plots
```

**参数说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-d` | . | CSV 文件所在目录 |
| `-o` | 同 CSV 目录 | 图表输出目录 |

**生成的图表：**

| 文件名 | 内容 |
|--------|------|
| `all_cpu.png` | 所有服务 CPU 使用率对比 |
| `all_memory.png` | 所有服务内存使用量 + 百分比 |
| `all_network.png` | 所有服务网络 I/O |
| `all_block_io.png` | 所有服务磁盘 I/O |
| `heatmap.png` | 容器资源热力图（均值汇总） |
| `server_overview.png` | 服务器总览（CPU/内存/负载/磁盘） |
| `service_<名称>.png` | 每个服务类型的详细面板（CPU/内存/网络/磁盘） |

**多节点展示：**
- 同一服务类型的多个节点会画在同一张图中
- 不同节点使用不同颜色和线型区分
- 图例格式：`web (node1)`, `web (node2)`

---

### analyze_logs.py — 日志分析

从 Docker 容器日志或磁盘日志文件中解析检索管道耗时信息。

```bash
# 从 Docker 容器日志分析
python analyze_logs.py --containers ha-node1-web ha-node2-web --since 5m

# 从磁盘日志文件分析
python analyze_logs.py --log-files /path/to/ragflow_server.log

# 混合来源
python analyze_logs.py --containers ha-node1-web --log-files ./node2/logs/ragflow_server.log

# 保存 JSON 结果
python analyze_logs.py --containers ha-node1-web --since 10m --output-json analysis.json
```

**参数说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--containers` | [] | Docker 容器名称列表 |
| `--log-files` | [] | 日志文件路径列表 |
| `--since` | 空（不限） | Docker logs --since 参数（如 `10m`, `1h`） |
| `--output-json` | — | 保存 JSON 结果到文件 |

**前置条件——RAGFlow 源码打点：**

该工具需要 RAGFlow 源码中包含 `[RETRIEVAL_TIMING]` 日志行。在 `rag/nlp/search.py` 的 `Dealer.search()` 和 `Dealer.retrieval()` 方法中添加：

```python
import time
import logging

# 在 search() 中:
t0 = time.perf_counter()
# ... embedding 编码 ...
logging.info(f"[RETRIEVAL_TIMING] step=embedding elapsed={time.perf_counter() - t0:.3f}")

t1 = time.perf_counter()
# ... 文档检索 ...
logging.info(f"[RETRIEVAL_TIMING] step=doc_search elapsed={time.perf_counter() - t1:.3f} total={len(hits)}")

# 在 retrieval() 中:
t_total = time.perf_counter()
# ... 完整检索流程 ...
logging.info(f"[RETRIEVAL_TIMING] step=total elapsed={time.perf_counter() - t_total:.3f} chunks_returned={len(chunks)}")
```

**日志格式：**

```
[RETRIEVAL_TIMING] step=embedding elapsed=0.123
[RETRIEVAL_TIMING] step=doc_search elapsed=0.045 total=256
[RETRIEVAL_TIMING] step=rerank_model elapsed=0.089 chunks=64
[RETRIEVAL_TIMING] step=total elapsed=0.267 chunks_returned=30
```

**输出报告示例：**

```
======================================================================
  RAGFlow 检索管道耗时分析
======================================================================

  数据来源: container:ha-node1-web
  总记录数: 342

  步骤                     次数    平均     中位     P95     最小     最大     占比
  -------------------- ------ -------- -------- -------- -------- -------- --------
  embedding              342    0.123    0.118    0.201    0.089    0.312    46.1%
  doc_search             342    0.045    0.042    0.078    0.031    0.120    16.9%
  rerank_model           342    0.089    0.085    0.145    0.052    0.234    33.3%
  total                  342    0.267    0.258    0.412    0.198    0.623        -

  --- 耗时分解 ---
  已统计步骤耗时总和: 0.257s
  最大瓶颈: embedding (平均 0.123s, 占已统计时间的 47.9%)
  未覆盖耗时: 0.010s (3.7%)
  (包括: 结果组装、文档聚合、子块合并、网络传输等)
======================================================================
```

---

## 配置文件格式

`bench_config.json` 由 `run_bench.py` 自动生成，也可以手动创建：

```json
{
  "base_url": "http://localhost:18080",
  "api_key": "ragflow-xxxx",
  "kb_queries": [
    ["知识库ID1", "查询文本1"],
    ["知识库ID2", "查询文本2"]
  ],
  "retrieval": {
    "concurrency": 10,
    "duration": 30,
    "top_k": 1024,
    "similarity_threshold": 0.2,
    "vector_similarity_weight": 0.3,
    "verify_ssl": true
  },
  "embedding": {
    "enabled": false,
    "api_url": "",
    "api_key": "",
    "api_format": "openai",
    "model": "text-embedding-ada-002",
    "input_text": "测试文本",
    "concurrency": 5,
    "request_count": 20,
    "verify_ssl": true
  },
  "monitor": {
    "enabled": true,
    "interval": 2,
    "duration": 60,
    "containers": ["ha-node1-web", "ha-node2-web", "ha-node1-worker", "ha-node2-worker"]
  },
  "log_analysis": {
    "enabled": true,
    "containers": ["ha-node1-web", "ha-node2-web"],
    "log_files": [],
    "since": ""
  },
  "output_dir": "./bench-output"
}
```

所有单工具都支持 `--config` 参数直接加载配置文件：

```bash
python bench_retrieval.py --config bench_config.json
python bench_embedding.py --config bench_config.json
python analyze_logs.py --config bench_config.json
```

---

## 多节点部署支持

所有工具原生支持多节点 HA 部署场景：

| 工具 | 多节点支持方式 |
|------|--------------|
| `bench_retrieval.py` | 通过 LB 入口压测，自动覆盖所有节点 |
| `bench_embedding.py` | 通过 LB 入口测试 |
| `monitor_resources.sh` | `-c` 指定多个容器名称 |
| `plot_monitor.py` | 自动按服务类型分组，多节点同图对比 |
| `analyze_logs.py` | `--containers` 指定多个容器，聚合分析 |

### 多节点压测示例

```bash
# 1. 同时监控所有节点的 web 和 worker
./monitor_resources.sh \
    -c "ha-node1-web ha-node1-worker ha-node2-web ha-node2-worker" \
    -i 2 -d 180 -o ./data &

# 2. 通过 LB 压测
python bench_retrieval.py \
    --base-url http://<LB地址>:18080 \
    --api-key ragflow-xxxx \
    --kb <KB_ID> --query "测试" \
    --concurrency 50 --duration 120 \
    --output-json ./data/retrieval.json

# 3. 聚合分析所有节点日志
python analyze_logs.py \
    --containers ha-node1-web ha-node2-web \
    --since 3m --output-json ./data/analysis.json

# 4. 生成图表
python plot_monitor.py -d ./data -o ./data
```

---

## 结果解读

### 关键指标

| 指标 | 含义 | 健康参考值 |
|------|------|-----------|
| **QPS** | 每秒处理请求数 | 越高越好，受并发和延迟影响 |
| **成功率** | 成功请求占比 | 应保持 >= 99% |
| **P50 延迟** | 50% 请求的响应时间 | 应接近平均延迟 |
| **P95 延迟** | 95% 请求的响应时间 | 应 <= 2x P50 |
| **P99 延迟** | 99% 请求的响应时间 | 应 <= 3x P50 |

### 性能问题排查

| 现象 | 可能原因 | 建议 |
|------|---------|------|
| P95/P99 远大于 P50 | 存在排队或资源竞争 | 降低并发或扩容 |
| 大量 502 错误 | 后端连接池耗尽 | 检查 ES 连接池、ASGI backlog 设置 |
| 成功率 < 95% | 服务过载或配置问题 | 检查容器资源和日志 |
| QPS 不随并发增长 | 达到瓶颈 | 通过日志分析定位瓶颈步骤 |
| 内存持续增长 | 可能内存泄漏 | 检查 worker 进程内存使用 |
| embedding 步骤耗时高 | 嵌入模型性能不足 | 考虑升级硬件或换模型 |
| doc_search 步骤耗时高 | ES/Infinity 查询慢 | 检查索引优化、连接池配置 |

---

## 性能诊断实战指南

本节基于真实 HA 环境（双节点，RAGFlow v0.24.0，智谱 AI embedding-3 模型）的完整诊断过程编写。

### 诊断流程

1. **初步压测** → 确定 QPS 天花板和基本健康状况
2. **RAGFlow 源码打点** → 精确测量管道各步骤耗时
3. **资源监控** → 观察 CPU、内存、线程池使用
4. **日志分析** → 定位耗时占比最高的步骤
5. **逐层优化** → 按瓶颈优先级依次修复

### RAGFlow 源码打点

`analyze_logs.py` 需要 RAGFlow 源码包含 `[RETRIEVAL_TIMING]` 日志。在 `rag/nlp/search.py` 中需要添加以下打点：

**Dealer.search() 方法：**
```python
import time, logging, threading

# embedding 编码耗时
t_emb_start = time.perf_counter()
matchDense = await self.get_vector(qst, emb_mdl, topk, req.get("similarity", 0.1))
t_emb_elapsed = time.perf_counter() - t_emb_start
logging.info(f"[RETRIEVAL_TIMING] step=embedding elapsed={t_emb_elapsed:.4f}")

# 文档检索耗时
t_search_start = time.perf_counter()
res = await thread_pool_exec(self.dataStore.search, ...)
t_search_elapsed = time.perf_counter() - t_search_start
logging.info(f"[RETRIEVAL_TIMING] step=doc_search elapsed={t_search_elapsed:.4f} total={total} active_threads={threading.active_count()}")
```

**Dealer.retrieval() 方法：**
```python
# 入口：并发计数 + 总计时开始
global _concurrent_requests
with _concurrent_lock:
    _concurrent_requests += 1
    current_concurrency = _concurrent_requests
t_total_start = time.perf_counter()

# Rerank 耗时
t_rerank_start = time.perf_counter()
sim, tsim, vsim = self.rerank(...)  # 或 self.rerank_by_model(...)
t_rerank_elapsed = time.perf_counter() - t_rerank_start
logging.info(f"[RETRIEVAL_TIMING] step=rerank_hybrid elapsed={t_rerank_elapsed:.4f} chunks={sres.total}")

# 出口：总计时 + 并发计数
t_total_elapsed = time.perf_counter() - t_total_start
with _concurrent_lock:
    _concurrent_requests -= 1
logging.info(f"[RETRIEVAL_TIMING] step=total elapsed={t_total_elapsed:.4f} chunks_returned={n} concurrent={current_concurrency}")
```

**注意：** `retrieval()` 方法中有 3 处 early return（空问题、零结果、零过滤），每处都需要添加 total 计时日志。

### 管道耗时分析示例

```
======================================================================
  RAGFlow 检索管道耗时分析
======================================================================
  步骤                  次数     平均      P95       最大      占比
  -------------------- ------ -------- -------- -------- --------
  embedding              1440    0.556    0.846    1.322    63.5%
  doc_search             1424    0.157    0.364    2.281    18.0%
  rerank_hybrid          1416    0.003    0.006    0.029     0.3%
  total                  1416    0.875    1.474    2.789        -
  --- 耗时分解 ---
  最大瓶颈: embedding (平均 0.556s, 占已统计时间的 77.6%)
  未覆盖耗时: 0.159s (18.2%)
======================================================================
```

### 典型瓶颈及解决方案

| 瓶颈 | 症状 | 根因 | 解决方案 |
|------|------|------|---------|
| **外部 Embedding API** | embedding 步骤占 60%+ | 每次请求调用远程 API 耗时 500ms+ | 部署本地 embedding 模型（BGE-M3 等），延迟可降至 <10ms |
| **ES 连接池不足** | doc_search 高方差（CV>2） | 默认 connections_per_node=10 | 调至 50，历史数据 QPS 可提升 4-5x |
| **Web 节点内存不足** | 大量 502、容器 OOM | mem_limit: 1g 不够 | 至少 2GB |
| **Quart 单进程** | QPS 不随并发增长 | 单进程 event loop 饱和 | 增加 web 节点数水平扩容 |
| **线程池竞争** | 高并发时延迟非线性增长 | 线程池共享，embedding 阻塞线程 | 增大 THREAD_POOL_MAX_WORKERS 或改用异步调用 |

### 压测结果参考（双节点 HA，智谱 embedding-3）

| 并发 | QPS | P50 | P95 | 成功率 |
|:---:|:---:|:---:|:---:|:---:|
| 5 | 8.0 | 0.565s | 0.729s | 100% |
| 15 | 19.5 | 0.746s | 0.947s | 100% |
| 30 | 21.9 | 1.319s | 1.784s | 100% |
| 50 | 20.2 | 2.367s | 2.835s | 100% |

> QPS 天花板 ~22，在 30 并发时达到。继续增加并发只会增加延迟而不提升吞吐。

### 502 错误风暴

如果压测中出现大量 502 错误（成功率陡降），通常原因：

1. **Web 节点内存耗尽** — `docker stats` 检查内存是否 >95%
2. **后端服务未就绪** — 容器刚重启，Python server 初始化需 30s
3. **ES 连接池耗尽** — 检查 RAGFlow 错误日志中是否有 ES 连接超时
4. **LB 后端不健康** — 某个节点挂掉，LB 仍向其路由

**bench_retrieval.py 的退避机制**：当检测到快速返回的错误（<100ms），worker 会自动增加重试间隔（最高 1s），避免 502 风暴导致请求数膨胀。

---

## 常见问题

### Q: 提示 "Authentication error: API key is invalid!"


确认 API Key 正确且未过期。从数据库 `api_token` 表查询或通过 Web UI 重新生成。

### Q: 压测返回 502 错误

可能原因：
1. 后端服务连接池耗尽（参见 CLAUDE.md 中 ES 连接池调优建议）
2. 容器资源不足（检查 `docker stats`）
3. ASGI server backlog 太小（检查 Hypercorn/Quart 配置）

### Q: 日志分析没有找到 timing 记录

需要先在 RAGFlow 源码中添加 `[RETRIEVAL_TIMING]` 日志打点（参见 analyze_logs.py 章节）。打点后需要重启 RAGFlow 服务并重新执行压测。

### Q: 资源监控图表为空或数据不全

1. 确认监控时长覆盖了压测全程
2. 确认指定容器名称正确：`docker ps --filter "name=ha-" --format '{{.Names}}'`
3. 检查 CSV 文件是否存在：`ls -la <output_dir>/container_stats_*.csv`

### Q: Embedding 测试全部失败返回 404

确认目标 RAGFlow 版本是否支持 `/api/v1/embeddings` 端点。部分版本（如 v0.24.0）不提供独立的 Embedding API，需要使用第三方 Embedding 服务进行测试。

### Q: 在新服务器上如何快速开始

```bash
# 1. 克隆或复制项目到新服务器
# 2. 安装依赖
pip install httpx pandas matplotlib numpy

# 3. 获取 RAGFlow API Key（参考上方"获取 API 凭证"章节）
# 4. 获取知识库 ID

# 5. 快速验证
python bench_retrieval.py \
    --base-url http://<新服务器IP>:18080 \
    --api-key <API Key> \
    --kb <知识库ID> --query "测试查询" \
    --concurrency 2 --duration 5

# 6. 交互式完整测试
python run_bench.py
```

### Q: 离线（无网络）环境如何安装依赖

```bash
# 在有网络的环境中下载 wheel 包
pip download httpx pandas matplotlib numpy -d ./offline-packages

# 将 ./offline-packages 目录复制到离线服务器后安装
pip install --no-index --find-links ./offline-packages httpx pandas matplotlib numpy
```
