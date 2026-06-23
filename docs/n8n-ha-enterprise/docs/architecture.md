# n8n 企业版高可用部署架构

> 本文聚焦架构层面：组件职责、数据流、协议、决策依据、扩展点。
> 部署步骤与运维操作见同目录 [deployment-guide.md](./deployment-guide.md)。

## 目录

- [1. 设计目标](#1-设计目标)
- [2. 架构概览（C4 Level 1 - System Context）](#2-架构概览c4-level-1---system-context)
- [3. 容器拓扑（C4 Level 2 - Container）](#3-容器拓扑c4-level-2---container)
- [4. 组件职责](#4-组件职责)
- [5. 关键数据流](#5-关键数据流)
- [6. 高可用机制](#6-高可用机制)
- [7. 存储模型](#7-存储模型)
- [8. 协议与端口](#8-协议与端口)
- [9. 多节点模拟策略](#9-多节点模拟策略)
- [10. 资源限额模型](#10-资源限额模型)
- [11. 架构决策记录（ADR）](#11-架构决策记录adr)
- [12. 安全边界](#12-安全边界)
- [13. 扩展点与演进路径](#13-扩展点与演进路径)
- [14. 已知约束与权衡](#14-已知约束与权衡)

---

## 1. 设计目标

| 目标 | 衡量指标 | 实现方式 |
|------|---------|---------|
| **高可用** | main 进程单点故障不影响服务 | Multi-Main + 自动 leader 选举 |
| **横向扩展** | worker 可独立扩缩 | 队列模式 + 无状态 worker |
| **数据可靠** | 任务不丢失、凭据可解密 | Redis AOF+RDB、PG WAL、共享加密密钥 |
| **可观测** | 实例/队列/执行 全维度可见 | Prometheus + Grafana + n8n 内建 metrics |
| **故障隔离** | 单实例 OOM/崩溃 不拖垮集群 | 容器级 CPU/内存限额 + restart policy |
| **零侵入** | 不修改 n8n 源码、不依赖 k8s | 纯 Docker Compose + Traefik |

### 非目标

- 不替代 PostgreSQL / Redis 的高可用（这两者仍为单实例）
- 不实现跨数据中心灾备
- 不实现细粒度流量控制（金丝雀、A/B）

---

## 2. 架构概览（C4 Level 1 - System Context）

```
┌──────────────┐                     ┌──────────────────────────┐
│              │   HTTP/Webhook      │                          │
│  外部客户端  ├────────────────────▶│   n8n HA Cluster         │
│  (浏览器、   │◀────────────────────┤   (本部署)                │
│   第三方)    │   SSE / Response    │                          │
└──────────────┘                     └──────────┬───────────────┘
                                                │
                                                │ 依赖（读/写）
                                                ▼
                                     ┌──────────────────────┐
                                     │ 外部系统             │
                                     │ - SMTP / HTTP API    │
                                     │ - 数据库             │
                                     │ - SaaS（被自动化）   │
                                     └──────────────────────┘
```

边界：本部署对外只暴露 Traefik LB（5680/5681），其他所有组件均在内部网络。

---

## 3. 容器拓扑（C4 Level 2 - Container）

```
                          ┌─────────────────────────────────────┐
                          │         Docker Host (单机)          │
                          │                                     │
                          │  ┌───────────────────────────────┐  │
              5680/5681 ──┼─▶│ Traefik v3.1 (LB + Reverse)   │  │
                          │  └─────────────┬─────────────────┘  │
                          │                │ round-robin         │
                          │       ┌────────┴────────┐           │
                          │       ▼                 ▼           │
                          │ ┌──────────┐      ┌──────────┐       │
                          │ │ main-1   │      │ main-2   │       │
                          │ │ (leader/ │      │ (leader/ │       │
                          │ │ follower)│      │ follower)│       │
                          │ └─────┬────┘      └─────┬────┘       │
                          │       └──────┬──────────┘            │
                          │              │ enqueue               │
                          │       ┌──────▼──────┐                │
                          │       │ Redis 7     │ ◀── sticky     │
                          │       │ (BullMQ +   │     leader     │
                          │       │  election)  │     lock       │
                          │       └──────┬──────┘                │
                          │      ┌───────┼───────┐                │
                          │      ▼       ▼       ▼                │
                          │  ┌──────┐┌──────┐┌──────┐             │
                          │  │wk - 1││wk - 2││wk - 3│             │
                          │  └──┬───┘└──┬───┘└──┬───┘             │
                          │     └───────┼───────┘                 │
                          │             │                         │
                          │     ┌───────▼────────┐                │
                          │     │ PostgreSQL 15  │ ◀── shared     │
                          │     │ + MinIO (S3)   │     state      │
                          │     └────────────────┘                │
                          │                                     │
                          │  Observability:                     │
                          │  ┌────────────┐ ┌────────────┐       │
                          │  │Prometheus  │▶│ Grafana    │       │
                          │  └────────────┘ └────────────┘       │
                          └─────────────────────────────────────┘
```

### 容器清单（11 个常驻 + 1 个一次性）

| 容器 | 角色 | 启动命令 | 健康检查 |
|------|------|---------|---------|
| `n8n-ha-traefik` | LB / 反向代理 | `traefik` | `/ping` |
| `n8n-ha-postgres` | 共享数据库 | `postgres -c config_file=...` | `pg_isready` |
| `n8n-ha-redis` | 队列 + 选举 | `redis-server /usr/local/etc/redis/redis.conf` | `redis-cli ping` |
| `n8n-ha-minio` | S3 二进制数据 | `server /data --console-address :9001` | `mc ready local` |
| `n8n-ha-main-1` | API/UI/Webhook + leader | `n8n start` (默认) | `/healthz` 返回 `status:ok` |
| `n8n-ha-main-2` | 同上（互为热备） | `n8n start` | 同上 |
| `n8n-ha-worker-1` | 工作流执行 | `n8n worker --concurrency=10` | `/metrics` 暴露指标 |
| `n8n-ha-worker-2` | 同上 | 同上 | 同上 |
| `n8n-ha-worker-3` | 同上 | 同上 | 同上 |
| `n8n-ha-prometheus` | 指标采集 | `prometheus --config.file=...` | `/-/healthy` |
| `n8n-ha-grafana` | 可视化 | `/run.sh` | `/api/health` |
| `n8n-ha-minio-init` | 一次性 bucket 初始化 | `mc mb ...` | - |

---

## 4. 组件职责

### 4.1 Traefik（入口层）

**职责**：
- TLS 终结（生产环境）
- L7 路由（基于 Host / Path）
- 负载均衡到多个 main 实例
- 健康检查与故障剔除
- Sticky cookie（SSE 会话粘性）

**为何选 Traefik 而非 Nginx**：
- 自动服务发现（docker provider）
- 配置热更新（file provider watch）
- 内建 Prometheus metrics
- 声明式配置，无需 reload

**关键设计**：
- 使用 **file provider** 而非 docker labels 定义 `n8n_cluster` 服务（避免每个 main 容器独立创建 service 导致路由冲突）
- Sticky cookie 名 `n8n_sid`，保证 n8n UI 的 SSE 连接稳定路由到同一 main

### 4.2 n8n Main 进程

**两种角色（运行时动态切换）**：
- **Leader**：执行 regular 任务（API/UI/Webhook 接收）**+** at-most-once 任务（定时器、轮询、IMAP/RabbitMQ 等持久连接、执行历史清理）
- **Follower**：只执行 regular 任务

**启动时确定的职责**：
- 接收 webhook 并转换为执行任务
- 推送执行任务到 Redis BullMQ 队列
- 提供 UI 和 REST API
- 暴露 `/metrics` 给 Prometheus

### 4.3 n8n Worker 进程

**职责**：
- 从 Redis BullMQ 队列拉取执行任务
- 执行工作流（HTTP 调用、数据转换、节点编排）
- 将执行结果写回 PostgreSQL
- 暴露 `/metrics` 给 Prometheus

**无状态性**：worker 不持有工作流定义、凭据或会话——所有这些都从 PG/Redis 实时读取。这是水平扩展的前提。

**并发模型**：单进程多协程，由 `--concurrency=N` 控制同时处理的工作流数。

### 4.4 PostgreSQL（共享状态）

**存储内容**：
- 工作流定义（`workflow_entity`, `workflow_statistics`）
- 凭据（`credentials_entity`，加密存储）
- 执行历史（`execution_entity`, `execution_data`）
- 用户与权限（`user`, `project`, `role`）
- 设置（`settings`）

**写入特征**：
- 高频写入：`execution_data`（每次工作流执行）
- 低频写入：workflow 定义、凭据
- 中频读取：worker 每次执行都读取 workflow + credentials

### 4.5 Redis（消息总线）

**双重角色**：
1. **BullMQ 队列**：main 推送执行任务，worker 拉取
2. **Leader 选举锁**：multi-main 通过 Redis SET NX 实现分布式锁

**为什么不用单独的选举服务**：
- Redis 已经在架构中（BullMQ 依赖）
- n8n 内建基于 Redis 的 leader 选举
- 减少组件数量

### 4.6 MinIO（对象存储）

**职责**：存储工作流执行中的二进制数据（文件、图片、PDF 等）

**为什么需要外置**：
- Multi-main 模式下，多个 main 不能共享 `/home/node/.n8n` 卷
- 默认 filesystem 模式会导致 binary data 散落在各实例本地，无法跨节点访问

**注意**：S3 模式需要 Enterprise license；未激活时降级为 filesystem 模式。

### 4.7 Prometheus + Grafana（可观测性）

- **Prometheus**：pull 模式抓取所有 n8n/Traefik 的 `/metrics`
- **Grafana**：通过 provisioning 自动加载 Prometheus 数据源和看板

---

## 5. 关键数据流

### 5.1 用户请求流（UI / REST API）

```
浏览器
  │
  │ HTTP GET /workflow
  ▼
Traefik (5680)
  │
  │ 检查 sticky cookie n8n_sid
  │ round-robin 到 main-1 或 main-2
  ▼
n8n-main-X (5678)
  │
  │ 读取 PG workflow_entity
  │ 返回 JSON
  ▼
Traefik → 浏览器
```

**SSE 流（执行进度推送）**：
```
浏览器
  │ GET /rest/executions/:id/stream (SSE)
  ▼
Traefik ──sticky cookie──▶ 同一 main 实例
                              │
                              │ 保持长连接，推送进度事件
                              ▼
                          浏览器
```

### 5.2 Webhook 触发执行流

```
第三方服务
  │ POST /webhook/xxx
  ▼
Traefik (5680)
  │
  │ round-robin
  ▼
n8n-main-X (5678)
  │
  │ 1. 匹配 webhook → workflow
  │ 2. 构造 job payload
  │ 3. LPUSH bull:jobs {payload}
  ▼
Redis (BullMQ)
  │
  │ BRPOPLPUSH bull:jobs bull:jobs:active
  ▼
n8n-worker-Y (任意空闲)
  │
  │ 1. 读取 workflow + credentials 从 PG
  │ 2. 执行节点链
  │ 3. 写 execution_data 到 PG
  │ 4. 可选：写 binary 到 MinIO
  ▼
完成 → 回调 webhook（如果配置）
```

### 5.3 定时触发流（at-most-once）

```
                    Leader (main-1)
                         │
                         │ 每 60s 扫描 active workflows
                         │ 找到 cron 触发器到点的 workflow
                         │
                         ▼
                    推送 job 到 Redis
                         │
                         ▼
                    Worker 执行
```

**关键**：只有 leader 跑定时器，避免重复触发。如果 leader 挂了，follower 在 5s 内接管。

### 5.4 Leader 选举流

```
main-1 启动 ──▶ 尝试 SET NX lock:leader main-1 TTL=5s ──▶ 成功 → 成为 leader
                                                           │
                                                           │ 每 2s EXPIRE 续约
                                                           ▼
main-2 启动 ──▶ 尝试 SET NX lock:leader main-2 TTL=5s ──▶ 失败 → 成为 follower
                                                           │
                                                           │ 每 1s 检查锁是否存在
                                                           ▼
                                                      锁消失 → 尝试升级
```

**关键参数**：
- 锁 TTL：5s（main 心跳）
- 续约间隔：2s
- 检查间隔：1s
- 实际 failover 时间：5-10s

### 5.5 监控数据流

```
n8n instances ──┐
Traefik        ──┼──▶ /metrics (HTTP GET, 15s 间隔) ──▶ Prometheus ──▶ Grafana
                │                                            │
                │                                            ▼
                │                                       Alertmanager (可选)
                │
                └──▶ 指标类型：
                     - n8n_workflow_duration_seconds (histogram)
                     - n8n_workflow_failed_total (counter)
                     - n8n_active_workflow_count (gauge)
                     - n8n_process_cpu_usage / rss_bytes
                     - traefik_entrypoint_requests_total
```

---

## 6. 高可用机制

### 6.1 故障场景与恢复

| 故障 | 检测 | 恢复 | 业务影响 |
|------|------|------|---------|
| 单个 main 进程崩溃 | Traefik healthcheck（10s 间隔） | Traefik 剔除，docker restart | 0（其他 main 接管） |
| Leader main 崩溃 | Redis 锁 TTL 过期（5s） | Follower 抢锁升级 | at-most-once 任务暂停 5-10s |
| 单个 worker 崩溃 | BullMQ stalled-job 检测 | 任务回到队列，其他 worker 拉取 | 该 worker 的在跑任务重试 |
| PostgreSQL 重启 | n8n DB 连接错误 | n8n 自动重连 | 服务中断 = PG 启动时间 |
| Redis 重启 | n8n queue 连接错误 | n8n 自动重连 + leader 重新选举 | 队列任务丢失（AOF 减轻） |
| Traefik 崩溃 | 端口不可达 | docker restart | 整个集群不可达直到恢复 |
| 宿主机宕机 | 全部不可达 | 需要外部监控告警 | **单点故障（本部署的硬约束）** |

### 6.2 故障切换时间线（main 故障）

```
T+0s    main-1 进程崩溃
T+0s    Traefik 标记 main-1 为不健康（实时探测失败）
T+0-10s Traefik 从负载均衡池中剔除 main-1
T+10s   后续请求全部路由到 main-2（用户无感知）
T+5s    Redis leader 锁 TTL 过期
T+5-6s  main-2 检测到锁消失，发起 SET NX
T+6s    main-2 成为新 leader，开始处理定时器
T+60s   docker 自动重启 main-1
T+90s   main-1 启动完成，加入集群作为 follower
T+90s   Traefik 重新加入 main-1 到负载均衡池
```

### 6.3 数据一致性

| 数据类型 | 一致性级别 | 机制 |
|---------|----------|------|
| Workflow 定义 | 强一致 | PostgreSQL 单一来源 |
| 凭据 | 强一致 | PostgreSQL + 共享 N8N_ENCRYPTION_KEY |
| 执行任务 | 至少一次 | BullMQ ACK + stalled-job 检测 |
| 执行状态 | 强一致 | PostgreSQL |
| Leader 身份 | 强一致 | Redis SET NX 原子操作 |
| Sticky 会话 | 弱一致 | Traefik cookie（main 故障后切换） |

---

## 7. 存储模型

### 7.1 数据存放位置

```
┌─────────────────────────────────────────────────────┐
│                  PostgreSQL (5435)                  │
│ ┌─────────────────────────────────────────────────┐ │
│ │ workflow_entity    ← 工作流定义                  │ │
│ │ workflow_statistics ← 执行统计                   │ │
│ │ credentials_entity ← 加密的凭据                  │ │
│ │ execution_entity   ← 执行元数据                  │ │
│ │ execution_data     ← 执行详情（JSON）            │ │
│ │ user / project / role ← 用户与权限               │ │
│ │ settings           ← 实例配置                    │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                   Redis (6379)                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ bull:jobs            ← 待执行任务队列            │ │
│ │ bull:jobs:active     ← 已领取未完成              │ │
│ │ bull:jobs:delayed    ← 延迟执行                  │ │
│ │ bull:jobs:stalled    ← 怀疑卡住（worker 死亡）   │ │
│ │ lock:leader          ← leader 选举锁             │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                MinIO (9002) / S3                    │
│ ┌─────────────────────────────────────────────────┐ │
│ │ bucket: n8n-data                                 │ │
│ │   └── binary data（工作流执行产生的文件）        │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│         本地文件卷（每实例独立，filesystem 模式）   │
│ ┌─────────────────┐ ┌─────────────────┐             │
│ │ volumes/main-1  │ │ volumes/main-2  │  ...        │
│ │ /home/node/.n8n │ │ /home/node/.n8n │             │
│ │  ├─ config      │ │  ├─ config      │             │
│ │  ├─ .license    │ │  ├─ .license    │             │
│ │  └─ (加密密钥)  │ │  └─ (加密密钥)  │             │
│ └─────────────────┘ └─────────────────┘             │
└─────────────────────────────────────────────────────┘
```

### 7.2 加密密钥策略

**关键约束**：所有 main/worker 必须共享同一 `N8N_ENCRYPTION_KEY`，否则：
- 在 main-1 创建的凭据，worker 无法解密
- Leader 切换后，新 leader 无法解密旧 leader 写入的凭据

**本部署实现**：
- 通过 `.env` 文件统一注入
- `init.sh` 生成 64 字符 hex 随机串
- 所有 service 通过 `env_file: [.env]` 加载

---

## 8. 协议与端口

### 8.1 外部暴露

| 端口 | 协议 | 服务 | 用途 |
|------|------|------|------|
| 5680 | HTTP | Traefik | n8n 统一入口（生产应启用 HTTPS） |
| 5681 | HTTPS | Traefik | 预留 TLS |
| 8889 | HTTP | Traefik Dashboard | 路由调试（生产应限制访问） |
| 5435 | TCP | PostgreSQL | 数据库（生产应移除外部映射） |
| 9002 | HTTP | MinIO API | S3 接口（生产应内网） |
| 9003 | HTTP | MinIO Console | Web 管理（生产应限制） |
| 9090 | HTTP | Prometheus | 指标查询（生产应限制） |
| 3001 | HTTP | Grafana | 可视化（生产应启用 HTTPS） |

### 8.2 容器内部通信（n8n-ha-net）

所有容器在 `172.31.0.0/16` 网段，通过容器名解析：

| 容器 | 内部地址 | 监听端口 |
|------|---------|---------|
| traefik | n8n-ha-net:traefik | 80, 443, 8080 |
| postgres | n8n-ha-net:postgres | 5432 |
| redis | n8n-ha-net:redis | 6379 |
| minio | n8n-ha-net:minio | 9000, 9001 |
| n8n-main-1 | n8n-ha-net:n8n-main-1 | 5678, 5679（Task Broker） |
| n8n-main-2 | n8n-ha-net:n8n-main-2 | 5678, 5679 |
| workers | n8n-ha-net:n8n-worker-{1,2,3} | 5678（metrics only） |
| prometheus | n8n-ha-net:prometheus | 9090 |
| grafana | n8n-ha-net:grafana | 3000 |

### 8.3 协议矩阵

| 源 → 目的 | 协议 | 端口 | 认证 |
|----------|------|------|------|
| 浏览器 → Traefik | HTTP | 5680 | Cookie (n8n session) |
| Traefik → n8n-main-X | HTTP | 5678 | 无（内网） |
| n8n-main → PostgreSQL | TCP | 5432 | 用户名/密码 |
| n8n-main/worker → Redis | TCP | 6379 | Redis 密码 |
| n8n-main/worker → MinIO | HTTP | 9000 | Access Key/Secret |
| Prometheus → 所有 n8n | HTTP | 5678 → /metrics | 无 |
| Grafana → Prometheus | HTTP | 9090 | 无 |

---

## 9. 多节点模拟策略

由于使用单台宿主机，本部署通过以下手段模拟多节点分布式部署：

| 维度 | 模拟方式 | 真实多机部署的差异 |
|------|---------|------------------|
| **网络隔离** | 所有容器加入 `n8n-ha-net` bridge 网络 | 真实多机用物理网络或 overlay |
| **主机标识** | 每个服务独立 `hostname`（n8n-main-1、n8n-main-2） | 真实主机名 |
| **进程隔离** | 每个服务独立容器 + 独立 PID 命名空间 | 独立 OS 进程 |
| **资源隔离** | `deploy.resources.limits` 限制 CPU/内存 | 物理资源隔离 |
| **故障隔离** | docker `restart: unless-stopped` | systemd / supervisor |
| **文件系统** | 每实例独立 volume 路径 | 独立磁盘 |
| **日志** | docker logs（per-container） | 主机日志聚合 |

### 模拟的局限

1. **网络延迟**：容器间延迟 < 0.1ms，真实跨机 1-5ms（影响 leader 选举超时配置）
2. **故障域**：宿主机宕机 = 全部宕机（真实多机能跨机存活）
3. **资源竞争**：所有容器共享宿主机内核调度器
4. **网络分区**：bridge 网络不会出现分区（真实多机可能）

### 真实多机部署的迁移要点

```bash
# 1. 把每个 service 拆到独立 docker-compose.yml
#    例如 host1: docker-compose.main-1.yml
#         host2: docker-compose.main-2.yml

# 2. PostgreSQL/Redis/MinIO 单独部署或用托管服务
#    （RDS、Elasticache、S3）

# 3. 替换内部容器名为内网 IP
#    DB_POSTGRESDB_HOST=10.0.1.10 (而不是 postgres)

# 4. 在 Traefik 配置中改用真实 IP
#    servers:
#      - url: http://10.0.1.11:5678  # main-1
#      - url: http://10.0.1.12:5678  # main-2

# 5. WEBHOOK_URL 改为公网域名
#    WEBHOOK_URL=https://n8n.example.com/
```

---

## 10. 资源限额模型

### 10.1 资源分配（总计）

| 服务 | CPU | 内存 | 备注 |
|------|-----|------|------|
| n8n-main-1 | 2.0 | 2 GB | API/UI/Webhook |
| n8n-main-2 | 2.0 | 2 GB | API/UI/Webhook |
| n8n-worker-1 | 1.5 | 1.5 GB | 工作流执行 |
| n8n-worker-2 | 1.5 | 1.5 GB | 工作流执行 |
| n8n-worker-3 | 1.5 | 1.5 GB | 工作流执行 |
| PostgreSQL | - | - | shared_buffers=2GB（内部管理） |
| Redis | - | - | maxmemory=512MB |
| Traefik | - | - | 默认（约 100MB） |
| MinIO | - | - | 默认 |
| Prometheus | - | - | TSDB 15d 保留 |
| Grafana | - | - | 默认 |
| **总计（n8n 部分）** | **8.5 核** | **8.5 GB** | - |

### 10.2 容量规划公式

```
worker 总并发 = worker 数 × 单 worker concurrency = 3 × 10 = 30 并发工作流

理论吞吐上限 = worker 总并发 / 平均工作流执行时长
            = 30 / 5s = 6 workflows/s
```

**扩容建议**：
- CPU 使用率持续 > 70% → 加 worker
- 队列长度持续 > 50 → 加 worker 或提高单 worker concurrency
- PG `pg_stat_activity.count` > 80% × max_connections → 提升连接上限

---

## 11. 架构决策记录（ADR）

### ADR-001: 选择 Docker Compose 而非 Kubernetes

**背景**：用户明确要求只能用 docker-compose。

**决策**：使用 docker-compose v2 + 自定义 bridge 网络。

**后果**：
- ✅ 部署简单，无 k8s 学习成本
- ✅ 配置文件可读性好
- ❌ 无法跨宿主机（除非用 docker swarm）
- ❌ 滚动更新需手动操作

### ADR-002: 选择 Traefik 而非 Nginx

**背景**：需要 L7 负载均衡 + 健康检查 + 服务发现。

**决策**：使用 Traefik v3.1。

**理由**：
- 内建 docker provider，自动发现服务
- file provider 支持热更新
- 原生支持 sticky cookie + 主动健康检查
- 内建 Prometheus metrics，无需额外 exporter

**替代方案**：
- Nginx + nginx-vts-exporter：更稳定但配置繁琐
- HAProxy：性能略好但学习曲线陡

### ADR-003: 使用 file provider 定义 n8n_cluster

**背景**：Traefik 可以通过 docker labels 或 file 配置定义服务。

**决策**：n8n_cluster 服务通过 `config/traefik/dynamic/dynamic.yml` 定义。

**理由**：
- docker labels 会为每个 main 容器独立创建 service，导致同 Host 多 router 冲突
- file provider 可以将多个 server URL 聚合到一个 loadBalancer service
- 配置集中，易于审计

**代价**：
- 新增 main 实例需手动编辑 dynamic.yml（不像 docker labels 自动）
- 通过 `watch: true` 实现热加载

### ADR-004: 默认 filesystem 模式，license 激活后切 S3

**背景**：S3 模式需要 Enterprise license，但用户可能尚未购买。

**决策**：`.env` 中 `N8N_BINARY_DATA_MODE=filesystem` 默认值；激活 license 后改 `s3`。

**后果**：
- ✅ 无 license 也能完整启动
- ✅ 架构本身已就绪（MinIO 已部署）
- ⚠️ filesystem 模式下，binary data 散落在各实例本地（main-1 上传的文件 main-2 访问不到）

### ADR-005: Enterprise License 通过环境变量注入

**背景**：license 可以通过 UI 激活或环境变量激活。

**决策**：使用 `N8N_LICENSE_ACTIVATION_KEY` 环境变量。

**理由**：
- 可纳入版本控制（占位符 + git-secret）
- 重启即生效，无需人工 UI 操作
- 多实例一致

### ADR-006: PostgreSQL 不做 HA

**背景**：用户明确"数据库等服务不需要"高可用。

**决策**：PG 单实例 + AOF/RDB 备份。

**后果**：
- ✅ 部署简单
- ❌ PG 是单点（挂了整个集群不可用）
- ⚠️ 真实生产应升级到 PG 主从或托管服务（RDS、Cloud SQL）

### ADR-007: Worker healthcheck 使用 /metrics 而非 /healthz

**背景**：worker 模式下 n8n 不暴露 /healthz（返回 404），但 /metrics 正常。

**决策**：worker 的 healthcheck 改为检查 `/metrics` 是否返回 `n8n_process_cpu` 指标。

**理由**：
- worker 进程是 Node.js 应用，主要职责是消费队列
- `/metrics` 端点证明 worker 进程在跑且 HTTP server 正常
- 比起 `pgrep` 更能反映"服务可用"

---

## 12. 安全边界

### 12.1 信任域

```
┌────────────────────────────────────────────────────┐
│  外部网络（不可信）                                │
│    │                                              │
│    │ 仅 5680/5681 开放                            │
│    ▼                                              │
│  Traefik（边界）                                  │
│    │                                              │
│    │ 内部网络 n8n-ha-net（半信任）                │
│    │ 容器间默认互通，无 mTLS                      │
│    ▼                                              │
│  PostgreSQL/Redis/MinIO（凭据保护）               │
│    依赖密码认证，但传输未加密                      │
└────────────────────────────────────────────────────┘
```

### 12.2 凭据存储

| 凭据类型 | 存储位置 | 加密 |
|---------|---------|------|
| PostgreSQL 密码 | `.env` | 无（git-ignored） |
| Redis 密码 | `.env` + `redis.conf` | 无 |
| MinIO 密钥 | `.env` | 无 |
| n8n 加密密钥 | `.env` | 无（**丢失即所有凭据失效**） |
| n8n 凭据（用户的） | PostgreSQL `credentials_entity` | 用 N8N_ENCRYPTION_KEY AES 加密 |
| Enterprise License | `.env` | n8n SDK 内部验证 |

### 12.3 生产环境加固清单

- [ ] 移除 PG/Redis/MinIO 的外部端口映射
- [ ] Traefik 启用 HTTPS + 自动证书
- [ ] 启用 `N8N_SECURE_COOKIE=true`
- [ ] 限制 8889/9090/3001 端口的访问源
- [ ] 使用 Docker Secrets 替代 `.env`
- [ ] 集成外部密钥管理（HashiCorp Vault）
- [ ] 启用审计日志（n8n Enterprise Log Streaming）

---

## 13. 扩展点与演进路径

### 13.1 短期演进（无架构变更）

| 需求 | 操作 |
|------|------|
| 提升吞吐 | 增加 worker 实例（修改 docker-compose.yml 复制 n8n-worker-N） |
| 提升 main 容错 | 增加 main-3（需更新 Traefik dynamic.yml） |
| 启用 S3 binary data | `.env` 切换 `N8N_BINARY_DATA_MODE=s3`，重建服务 |
| 启用 Log Streaming | UI → Settings → Log Streaming → 配置目标 |
| 启用 SSO | UI → Settings → SSO → 配置 SAML/LDAP |

### 13.2 中期演进（架构微调）

| 需求 | 改动 |
|------|------|
| PostgreSQL HA | 引入 Patroni / Stolon，或迁移到托管 RDS |
| Redis HA | 引入 Redis Sentinel 或 Cluster |
| MinIO HA | MinIO Distributed Mode（4+ 节点） |
| 跨主机部署 | 迁移到 Docker Swarm 或 k3s |
| 集中日志 | 引入 Loki + Promtail |

### 13.3 长期演进（架构重塑）

| 需求 | 改动 |
|------|------|
| 真正的 multi-region | 拆分 PG/Redis 到独立集群（跨 region 复制） |
| Workflow 版本管理 | 启用 n8n Git 同步（Enterprise） |
| 多租户隔离 | 启用 n8n Projects + RBAC（Enterprise） |
| 自定义节点开发 | 部署 n8n External Task Runner |
| 工作流 Marketplace | 集成 n8n Templates API |

---

## 14. 已知约束与权衡

### 14.1 单宿主机约束

- 宿主机宕机 = 整个集群不可用
- 资源竞争：所有容器共享宿主机 CPU/内存/IO
- 无法模拟真实网络分区

### 14.2 License 依赖

- Multi-main 功能需要 Enterprise license
- S3 binary data 模式需要 Enterprise license
- 未激活时降级为"架构就绪"，部分功能受限

### 14.3 数据库单点

- PostgreSQL 单实例，无主从
- Redis 单实例，无 Sentinel
- 这两者故障 = 集群不可用（用户明确接受）

### 14.4 监控未告警

- 本部署只采集，未配置告警规则
- 生产应集成 Alertmanager + 通知渠道

### 14.5 备份未自动化

- 提供了备份脚本示例，但未配置定时任务
- 生产应配置 crontab 或 systemd timer

---

## 附录 A：架构图标约定

本文档使用的图例：

| 符号 | 含义 |
|------|------|
| `▶` / `▼` | 数据流方向 |
| `──X──▶` | 跨越信任边界 |
| `(healthy)` | 已通过健康检查 |
| `[...]` | 配置项引用 |
| `{...}` | 数据负载 |

## 附录 B：参考资料

- [n8n Queue Mode 官方文档](https://docs.n8n.io/hosting/scaling/queue-mode)
- [n8n Multi-main Setup](https://docs.n8n.io/hosting/scaling/queue-mode#multi-main-setup)
- [C4 Model](https://c4model.com/)
- [The Twelve-Factor App](https://12factor.net/)
- [Traefik v3 Documentation](https://doc.traefik.io/traefik/v3.1/)
- [BullMQ Architecture](https://docs.bullmq.io/architecture)

---

**文档版本**：v1.0  
**最后更新**：2026-06-22  
**基于部署**：`/home/yangxiang/deployed-services/n8n-ha-enterprise/`
