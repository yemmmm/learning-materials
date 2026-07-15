# RAGFlow Retrieval API 压测工具集

对 RAGFlow 检索 API 进行全维度性能测试，支持资源监控、日志分析和交互式配置。

## 快速开始

```bash
# 安装依赖
uv sync

# 交互式执行（推荐）
python run_bench.py
```

首次运行会引导你配置所有参数（API 地址、知识库、并发数、监控选项等），
配置保存在 `bench_config.json`。再次运行时会展示当前配置，询问是否修改。

## 工具概览

| 脚本 | 功能 |
|------|------|
| `run_bench.py` | **主控脚本** — 交互式配置 + 编排所有测试阶段 |
| `bench_retrieval.py` | 检索 API 并发压测 (`/api/v1/retrieval`) |
| `bench_embedding.py` | Embedding 模型并发能力测试 |
| `monitor_resources.sh` | Docker 容器 + 服务器资源监控 (CPU/内存/网络/磁盘) |
| `plot_monitor.py` | 资源监控数据可视化（生成图表） |
| `analyze_logs.py` | 检索管道耗时分析（从日志提取 timing 信息） |

## 功能特性

### 1. 交互式配置

- 首次执行：逐步配置所有参数
- 再次执行：展示当前参数，可选择修改或直接执行
- 配置文件持久化 (`bench_config.json`)

### 2. 检索 API 压测

```bash
python bench_retrieval.py \
    --base-url http://localhost:18080 \
    --api-key ragflow-xxxx \
    --kb kb_id_1 --query "查询文本" \
    --concurrency 10 --duration 30 \
    --output-json results.json
```

- 支持多知识库同时压测
- 精确的 P50/P95/P99 延迟统计
- 错误分布分析
- JSON 结果导出

### 3. Embedding 模型并发测试

```bash
python bench_embedding.py \
    --api-url https://api.openai.com/v1/embeddings \
    --api-key sk-xxxx \
    --model text-embedding-ada-002 \
    --concurrency 5 --count 20
```

- 短时间少量请求，避免触发风控
- 支持 OpenAI 兼容和 RAGFlow 内部 API 格式
- 并发排队分析（前后半段延迟对比）
- 高并发/高请求数时自动警告

### 4. 资源监控

```bash
./monitor_resources.sh -i 2 -d 120 -o ./data
./monitor_resources.sh -c "ha-node1-web ha-node2-web" -i 2 -d 120
```

- Docker 容器: CPU%、内存、网络 I/O、块 I/O
- 服务器: CPU%、内存、负载、磁盘
- CSV 输出，供可视化分析

### 5. 检索管道耗时分析

```bash
python analyze_logs.py --containers ha-node1-web ha-node2-web --since 5m
python analyze_logs.py --log-files /path/to/ragflow_server.log
```

- 解析 `[RETRIEVAL_TIMING]` 日志，按步骤聚合耗时
- 步骤: embedding → doc_search → rerank → total
- 自动识别最大瓶颈
- 依赖: RAGFlow 源码需添加 timing 日志（修改 `rag/nlp/search.py`）

### 6. 资源图表

```bash
python plot_monitor.py -d ./bench-data -o ./plots
```

- 所有服务 CPU/内存/网络/磁盘对比图
- 按服务类型分组图（多节点同图）
- 容器资源热力图、服务器总览图

## 多节点支持

所有工具均支持多节点部署场景：

- `monitor_resources.sh` 监控多个容器
- `analyze_logs.py` 聚合多个容器的日志
- `plot_monitor.py` 按服务类型分组，用颜色和线型区分节点
- `bench_retrieval.py` 通过 LB 入口压测

## 推荐工作流

```bash
# 一键执行所有测试
python run_bench.py

# 或分步执行：
# 终端1: 启动监控
./monitor_resources.sh -i 2 -d 120 -o ./data

# 终端2: 启动压测
python bench_retrieval.py --base-url http://localhost:18080 --api-key ragflow-xxx --kb <id> --query "test" --concurrency 20 --duration 90 --output-json ./data/retrieval.json
python bench_embedding.py --api-url https://api.openai.com/v1/embeddings --api-key sk-xxx --model text-embedding-ada-002 --concurrency 5 --count 20 --output-json ./data/embedding.json

# 分析日志
python analyze_logs.py --containers ha-node1-web ha-node2-web --since 3m --output-json ./data/analysis.json

# 生成图表
python plot_monitor.py -d ./data -o ./data
```

## 依赖

```bash
uv sync  # 或 pip install httpx pandas matplotlib numpy
```
