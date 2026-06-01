# RAGFlow 分布式部署性能瓶颈识别测试方案

## 1. 测试目标

在分布式部署环境中，通过系统化的并发梯度压测，精确定位 RAGFlow 集群的性能瓶颈层级：

| 瓶颈层级 | 典型特征 | 排查方向 |
|----------|----------|----------|
| **Embedding API** | QPS 低且不随并发增长、低并发下 P50 即 >500ms | 扩容 API 配额 / 切换本地 Embedding |
| **ES 检索** | 低并发 P50 <100ms，高并发 P50 急剧增长 | 增大 ES 连接池 / 调整 ES 线程池 / 加 ES 节点 |
| **Web 服务层** | 出现 502/503 错误、CPU 满载 | 增加 Web 节点 / 增大内存 / 调整 accept 队列 |
| **网络带宽** | 延迟随并发线性增长，但 CPU/MEM 正常 | 检查带宽 / 升级网卡 / 减少 Embedding 向量维度 |

## 2. 测试架构

```
                    ┌──────────────────┐
                    │  bench_retrieval  │  压测机（任意一台可访问 LB 的机器）
                    │  (httpx async)    │
                    └────────┬─────────┘
                             │ HTTP
                    ┌────────▼─────────┐
                    │   Load Balancer   │  Nginx / HAProxy / Traefik
                    └──┬──────────┬─────┘
                       │          │
              ┌────────▼──┐  ┌───▼─────────┐
              │  Web Node1 │  │  Web Node2  │  每台运行 monitor.py
              │  + Worker  │  │  + Worker   │
              └─────┬──────┘  └──────┬──────┘
                    │                │
        ┌───────────┴────────────────┴───────────┐
        │         Infrastructure Layer           │
        │   MySQL · Redis · ES · MinIO           │
        └────────────────────────────────────────┘
```

## 3. 测试维度

### 3.1 模式一：检索压测（retrieval mode）

测试完整的检索管线：请求 → LB → Web 节点 → ES 检索 → Embedding API → 返回结果。

**目标**: 找到端到端 QPS 上限、最优并发数、瓶颈层级。

### 3.2 模式二：健康检查压测（health mode）

测试纯 HTTP 层吞吐：调用 `/api/v1/system/version`。

**目标**: 隔离 HTTP 层，确认瓶颈不在 nginx/Quart 层。

### 3.3 对比测试

通过 A/B 对比，量化单项改动的效果：

| 对比场景 | 改动 | 预期变化 |
|----------|------|----------|
| ES pool 10 vs 50 | `connections_per_node` | QPS +50~400% |
| 1 节点 vs 2 节点 | 移除/添加 Web 节点 | QPS ≈ 线性 |
| 远程 vs 本地 Embedding | Embedding 服务位置 | QPS +5~10x |
| Quart vs Hypercorn | 启动方式 | 错误率差异 |

## 4. 执行步骤

### 4.1 环境准备

```bash
# 1. 克隆脚本到压测机
git clone https://github.com/yemmmm/learning-materials.git
cd learning-materials/ragflow-perf-test

# 2. 安装依赖
pip install httpx

# 3. 编辑配置
cp config.env my_config.env
vim my_config.env  # 修改 URL、账号、KB IDs

# 4. 加载配置
source my_config.env
```

### 4.2 单机执行（最简单）

```bash
# 仅压测，不监控
source my_config.env
python3 bench_retrieval.py \
    --url "$RAGFLOW_URL" \
    --email "$RAGFLOW_EMAIL" \
    --password "$RAGFLOW_PASSWORD" \
    --kb-ids "$RAGFLOW_KB_IDS" \
    --concurrencies 10,30,50,100,200,500
```

### 4.3 全功能执行（推荐）

```bash
# 先 source 配置
source my_config.env

# 在所有 RAGFlow 节点上手动启动监控（在每台服务器上）:
#   python3 monitor.py --output /tmp/monitor_$(hostname).csv --interval 2

# 运行压测
bash run_test.sh

# 压测完成后，从各节点 scp 监控文件到压测机:
#   scp user@node1:/tmp/monitor_node1.csv results/<TAG>/
#   scp user@node2:/tmp/monitor_node2.csv results/<TAG>/

# 生成报告
python3 analyze.py --input results/<TAG> --output results/<TAG>/report.md
```

### 4.4 带 SSH 远程监控执行

```bash
# 配置监控主机（在 config.env 中设置）
export MONITOR_HOSTS="root@10.0.0.11:22:web1 root@10.0.0.12:22:web2 root@10.0.0.10:22:infra"

# 自动启动监控、压测、收集数据、生成报告
bash run_test.sh
```

## 5. 指标解读指南

### 5.1 QPS 曲线

```
QPS
 ^
 |     ┌──────── plateau (饱和点)
 |    ╱
 |   ╱
 |  ╱
 | ╱
 └──────────────────────> 并发

饱和点出现得越早 → 单个请求耗时越长 → Embedding API 是瓶颈
饱和点出现得越晚 → 系统并行度高 → Embedding API 延迟低
```

### 5.2 延迟百分位

| P50/P95 关系 | 含义 |
|-------------|------|
| P95/P50 < 2x | 请求处理均匀，无严重排队 |
| P95/P50 2-5x | 有排队但可控 |
| P95/P50 > 5x | 严重排队，尾部请求等待时间过长 |

### 5.3 错误类型

| 错误类型 | 根因 | 解决方案 |
|----------|------|----------|
| `client_timeout` | 请求在队列中等待过久 | 降低并发 / 加速 Embedding |
| `http_502` | Web 后端 accept 队列满 | 增加 Web 节点 / 切换 Quart app.run() |
| `http_503` | 所有后端不可用 | 检查 Web 节点健康状态 |
| `http_504` | nginx 等待后端超时 | 增大 proxy_read_timeout |
| `api_error` | Embedding API 返回错误 | 检查 API Key / 配额 |
| `connection_error` | TCP 连接被拒绝 | 检查目标服务是否启动 |

### 5.4 服务端资源

| 指标 | 健康范围 | 警告阈值 |
|------|----------|----------|
| CPU % | < 80% | > 90% 持续 |
| Memory % | < 80% | > 90% (OOM 风险) |
| Load (1m) | < CPU 核数 | > CPU 核数 × 2 |
| 网络 IO | < 80% 带宽 | > 90% 带宽 |
| Open FDs | < 10000 | > 50000 |

## 6. 预期输出示例

执行成功后，`results/<TAG>/` 目录结构：

```
results/20240601_120000/
├── summary.json           # 汇总数据（可直接用于分析）
├── report.md              # Markdown 格式分析报告
├── monitor_web1.csv       # web1 服务端资源时序数据
├── monitor_web2.csv       # web2 服务端资源时序数据
└── monitor_infra.csv      # 基础设施资源时序数据
```

### summary.json 关键字段

```json
{
  "test_config": {...},
  "rounds": [
    {
      "concurrency": 50,
      "qps": 64.5,
      "p50_s": 0.58,
      "p95_s": 2.38,
      "p99_s": 3.10,
      "success": 1935,
      "failure": 0,
      "error_distribution": {}
    }
  ],
  "bottleneck_analysis": {
    "findings": ["QPS 增长放缓 → 接近系统容量上限", ...],
    "cpu_bottleneck_probability": "低",
    "embedding_bottleneck_probability": "高",
    "es_bottleneck_probability": "低",
    "recommended_max_concurrency": 200,
    "estimated_max_qps": 64.5
  }
}
```

## 7. 排查决策树

```
QPS 随并发增长吗？
├── 是 → P50 < 100ms?
│   ├── 是 → 系统健康，瓶颈在 Embedding API（不可控）
│   └── 否 → 单次检索延迟高
│       ├── ES 搜索慢？→ 检查 ES 线程池、连接池
│       └── Embedding API 慢？→ 缩短向量维度 / 本地化部署
└── 否 → 出现错误？
    ├── 502 → Web 服务过载 → 加节点 / 检查 Quart 配置
    ├── 客户端超时 → 请求排队 → 降低并发 / 加速 Embedding
    └── API 错误 → Embedding API 限流 → 扩容配额
```
