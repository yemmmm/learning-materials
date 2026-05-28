# RAGFlow Retrieval API 压力测试工具

对 RAGFlow `/api/v1/retrieval` 接口进行并发压力测试，支持多知识库同时压测。

## 依赖

```bash
pip install httpx pandas matplotlib
```

或使用 uv：

```bash
uv pip install httpx pandas matplotlib
```

## 用法

### 单知识库压测

```bash
python bench_retrieval.py \
    --base-url http://localhost:18080 \
    --api-key ragflow-xxxxxxxx \
    --kb <dataset_id> \
    --query "你的查询文本" \
    --concurrency 10 \
    --duration 30
```

### 多知识库压测

每个 `--kb` 对应一个 `--query`，一一配对：

```bash
python bench_retrieval.py \
    --base-url http://localhost:18080 \
    --api-key ragflow-xxxxxxxx \
    --kb kb_id_1 --query "知识库一的查询" \
    --kb kb_id_2 --query "知识库二的查询" \
    --kb kb_id_3 --query "知识库三的查询" \
    --concurrency 20 \
    --duration 60
```

并发请求会在所有知识库之间轮流分配，实现均匀压测。

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--base-url` | 是 | - | RAGFlow 服务地址 |
| `--api-key` | 是 | - | API Key（`ragflow-` 前缀） |
| `--kb` | 是 | - | 知识库 ID，可多次指定 |
| `--query` | 是 | - | 查询文本，与 `--kb` 一一对应 |
| `--concurrency` | 否 | 10 | 并发数 |
| `--duration` | 否 | 30 | 压测持续时间（秒） |
| `--top-k` | 否 | 1024 | 检索 top_k 参数 |
| `--similarity-threshold` | 否 | 0.2 | 相似度阈值 |
| `--vector-similarity-weight` | 否 | 0.3 | 向量相似度权重 |

## 输出示例

```
============================================================
  RAGFlow Retrieval 压测报告
============================================================

  目标:        http://localhost:18080/api/v1/retrieval
  知识库:      abc123 (什么是机器学习?...)
  并发数:      10
  持续时间:    30.1s

  --- 请求统计 ---
  总请求数:    245
  成功:        243
  失败:        2
  成功率:      99.2%
  QPS:         8.14

  --- 延迟统计 (秒) ---
  最小:        0.102
  最大:        3.456
  平均:        1.234
  中位数:      1.100
  标准差:      0.456
  P95:         2.100
  P99:         2.890

============================================================
```

## 常见场景

### 测试 HA 集群负载均衡效果

通过 LB 入口压测，验证请求是否被分发到多个节点：

```bash
python bench_retrieval.py \
    --base-url http://localhost:18080 \
    --api-key ragflow-xxxx \
    --kb <id> --query "test query" \
    --concurrency 50 --duration 120
```

### 对比不同并发级别的性能

```bash
for c in 1 5 10 20 50; do
    echo "=== Concurrency: $c ==="
    python bench_retrieval.py \
        --base-url http://localhost:18080 \
        --api-key ragflow-xxxx \
        --kb <id> --query "test query" \
        --concurrency $c --duration 30
done
```

## 资源监控

压测过程中同步采集 Docker 容器 + 服务器资源数据。

### 采集数据

```bash
# 默认: 每5秒采样，持续300秒，自动检测 ha- 前缀容器
./monitor_resources.sh

# 自定义参数
./monitor_resources.sh -i 2 -d 600 -o ./data

# 指定容器
./monitor_resources.sh -c "ha-node1-web ha-node2-web ha-node1-worker ha-node2-worker"
```

输出两个 CSV 文件：
- `container_stats_<时间戳>.csv` — 容器 CPU、内存、网络 I/O、块 I/O
- `server_stats_<时间戳>.csv` — 服务器 CPU、内存、负载、磁盘

### 可视化

自动读取目录下所有 `container_stats_*.csv` 和 `server_stats_*.csv`，按服务类型分组绘图。

```bash
# 读取当前目录所有 CSV
python plot_monitor.py

# 指定 CSV 目录和输出目录
python plot_monitor.py -d ./bench-data -o ./plots
```

生成图表：

| 图表 | 说明 |
|------|------|
| `all_cpu.png` | 所有服务 CPU 使用率（多节点同图，按颜色+线型区分）|
| `all_memory.png` | 所有服务内存使用量和百分比 |
| `all_network.png` | 所有服务网络出入流量 |
| `all_block_io.png` | 所有服务磁盘读写 |
| `heatmap.png` | 所有容器资源热力图（最终快照）|
| `service_<名称>.png` | 按服务类型单独出图（如 `service_web.png` 含 node1+node2）|
| `server_overview.png` | 服务器 CPU、内存、负载、磁盘总览（合并所有采样数据）|

服务名解析规则：`ha-node1-web` → 服务类型 `web`、节点 `node1`；`ha-mysql` → 服务类型 `mysql`、节点 `infra`。多节点同类服务合并到同一张 `service_<名称>.png` 中，用不同颜色和线型区分节点。

### 推荐工作流：压测 + 监控并行

```bash
# 终端1: 启动监控
./monitor_resources.sh -i 5 -d 120 -o ./bench-data

# 终端2: 启动压测
python bench_retrieval.py \
    --base-url http://localhost:18080 \
    --api-key ragflow-xxxx \
    --kb <id> --query "test" \
    --concurrency 20 --duration 90

# 压测结束后，生成图表
python plot_monitor.py -d ./bench-data -o ./bench-data
```
