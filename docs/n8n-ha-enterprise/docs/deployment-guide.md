# n8n 企业版高可用部署与性能调优指南

> 本指南基于本地 Docker Compose 实战部署，完整实现了 n8n 企业版 Multi-Main Queue Mode 高可用架构。
> 适用于希望在单机或少量节点上模拟生产级 HA 拓扑的开发者与运维人员。

## 目录

- [1. 架构总览](#1-架构总览)
- [2. 前置条件](#2-前置条件)
- [3. 快速部署](#3-快速部署)
- [4. 拓扑与节点说明](#4-拓扑与节点说明)
- [5. 关键配置详解](#5-关键配置详解)
- [6. 性能调优](#6-性能调优)
- [7. 监控与可观测性](#7-监控与可观测性)
- [8. License 激活](#8-license-激活)
- [9. 扩缩容](#9-扩缩容)
- [10. 备份与恢复](#10-备份与恢复)
- [11. 安全加固](#11-安全加固)
- [12. 故障排查](#12-故障排查)
- [13. 生产环境上线检查清单](#13-生产环境上线检查清单)

---

## 1. 架构总览

### 1.1 社区版 vs 企业版

| 维度 | 社区版 Queue Mode | 企业版 Multi-Main |
|------|------------------|-------------------|
| main 进程 | 单点 | 多个（leader + follower，自动选举） |
| main 故障切换 | 不支持，服务中断 | 自动 failover，秒级恢复 |
| worker 水平扩展 | 支持 | 支持 |
| Webhook 高可用 | 单点 | 多 main 共担 |
| 二进制数据外置 | 需要 Enterprise | 需要 Enterprise |
| License | 不需要 | 需要 Enterprise License |

### 1.2 本部署的拓扑

```
                        外部请求
                          │
                          ▼
                ┌──────────────────────┐
                │ Traefik v3 LB :5680  │  ← 健康检查 + sticky session
                └──────────┬───────────┘
                           │ round-robin
              ┌────────────┴────────────┐
              ▼                          ▼
       ┌──────────────┐          ┌──────────────┐
       │ n8n-main-1   │          │ n8n-main-2   │   ← Multi-Main（leader/follower 自动选举）
       │ (leader/follower)│      │ (leader/follower)│
       └──────┬───────┘          └──────┬───────┘
              └──────────┬───────────────┘
                         │ 推送执行任务到 BullMQ
                  ┌──────▼──────┐
                  │  Redis 7    │  ← AOF + RDB 双持久化
                  │  (BullMQ)   │
                  └──────┬──────┘
                         │ 拉取任务
            ┌────────────┼────────────┐
            ▼            ▼            ▼
       ┌─────────┐  ┌─────────┐  ┌─────────┐
       │worker-1 │  │worker-2 │  │worker-3 │   ← 无状态，按需水平扩展
       └────┬────┘  └────┬────┘  └────┬────┘
            └─────────────┼─────────────┘
                       ┌──▼──┐           ┌──────┐
                       │ PG  │           │MinIO │   ← 共享存储
                       └─────┘           └──────┘

       可观测：Prometheus :9090 + Grafana :3001
```

### 1.3 模拟"多节点"的方式

由于使用单台宿主机，通过以下手段模拟多节点部署：

| 维度 | 实现方式 |
|------|---------|
| 网络隔离 | 所有容器加入 `n8n-ha-net` bridge 网络 |
| 主机标识 | 每个服务 `hostname` 唯一（n8n-main-1、n8n-main-2 等） |
| 容器隔离 | 每个服务独立 `container_name` + 独立数据卷 |
| 资源隔离 | 每个服务独立 CPU/内存限额 |
| 健康独立 | 每个服务独立 healthcheck + restart policy |

**生产环境多机部署**时，只需：
1. 把每个 service 放到不同物理机的 `docker-compose.yml`
2. 把 `localhost` 引用替换为各机器内网 IP
3. PostgreSQL/Redis/MinIO 单独部署或使用托管服务
4. 在每台机器上重复执行 `docker compose up -d <service-name>`

---

## 2. 前置条件

### 2.1 硬件建议

| 资源 | 最低 | 推荐 | 本部署 |
|------|------|------|--------|
| CPU | 4 核 | 8 核 | 按服务限额（main 2 核 × 2 + worker 1.5 核 × 3） |
| 内存 | 8 GB | 16 GB | PG 2GB + Redis 512MB + n8n ≈ 8GB |
| 磁盘 | 50 GB | 200 GB SSD | 取决于工作流执行历史 |
| 网络 | 单机即可 | 千兆内网 | 单机 bridge |

### 2.2 软件要求

```bash
# Docker Engine ≥ 24.0
docker --version

# Docker Compose v2
docker compose version

# OpenSSL（生成密钥）
openssl version
```

### 2.3 端口规划

本部署占用端口（已在 `DEPLOYED_SERVICES.md` 中登记）：

| 端口 | 服务 | 用途 |
|------|------|------|
| 5680 | Traefik HTTP | n8n 统一入口 |
| 5681 | Traefik HTTPS | 预留 |
| 8889 | Traefik Dashboard | 路由调试 |
| 5435 | PostgreSQL | 数据库 |
| 9002 | MinIO API | S3 接口 |
| 9003 | MinIO Console | Web 管理 |
| 9090 | Prometheus | 指标采集 |
| 3001 | Grafana | 可视化 |

---

## 3. 快速部署

### 3.1 一键启动

```bash
cd /home/yangxiang/deployed-services/n8n-ha-enterprise

# 1. 初始化（生成加密密钥、随机密码）
./scripts/init.sh

# 2. 启动集群（首次会拉镜像，约 5-10 分钟）
./scripts/start.sh

# 3. 健康检查（约 60-90s 后所有 n8n 实例就绪）
./scripts/healthcheck.sh
```

### 3.2 访问服务

| 服务 | URL | 凭据 |
|------|-----|------|
| n8n UI | http://localhost:5680 | 首次访问注册 owner 账号 |
| Traefik Dashboard | http://localhost:8889 | 无 |
| MinIO Console | http://localhost:9003 | 见 `.env` |
| Prometheus | http://localhost:9090 | 无 |
| Grafana | http://localhost:3001 | 见 `.env` |

### 3.3 停止与清理

```bash
./scripts/stop.sh                  # 停止（保留数据）
docker compose down                # 停止并删除容器（保留数据）
docker compose down -v             # ⚠️ 删除容器和数据卷
```

---

## 4. 拓扑与节点说明

### 4.1 节点清单

| 节点 | 容器名 | 角色 | 资源限额 | 关键参数 |
|------|--------|------|---------|---------|
| Traefik | n8n-ha-traefik | 负载均衡 | 默认 | sticky cookie + 健康检查 |
| PostgreSQL | n8n-ha-postgres | 共享数据库 | 默认 | `shared_buffers=2GB` |
| Redis | n8n-ha-redis | 队列 + leader 选举 | 默认 | AOF + RDB 持久化 |
| MinIO | n8n-ha-minio | S3 二进制数据 | 默认 | bucket `n8n-data` |
| n8n Main #1 | n8n-ha-main-1 | leader/follower | 2 CPU / 2GB | concurrency=20 |
| n8n Main #2 | n8n-ha-main-2 | leader/follower | 2 CPU / 2GB | concurrency=20 |
| n8n Worker #1 | n8n-ha-worker-1 | 执行节点 | 1.5 CPU / 1.5GB | concurrency=10 |
| n8n Worker #2 | n8n-ha-worker-2 | 执行节点 | 1.5 CPU / 1.5GB | concurrency=10 |
| n8n Worker #3 | n8n-ha-worker-3 | 执行节点 | 1.5 CPU / 1.5GB | concurrency=10 |
| Prometheus | n8n-ha-prometheus | 指标采集 | 默认 | 保留 15 天 |
| Grafana | n8n-ha-grafana | 可视化 | 默认 | 自动 provisioning |

### 4.2 Leader / Follower 选举机制

n8n Multi-Main 通过 Redis 实现 leader 选举：

1. 启动时，所有 main 实例向 Redis 注册
2. 第一个获得锁的成为 leader，处理 at-most-once 任务（定时器、轮询、IMAP/RabbitMQ 等持久连接）
3. 其他成为 follower，只处理 regular 任务（API/UI/Webhook）
4. leader 心跳超时（默认 5s），follower 自动接管

**关键环境变量**：
- `QUEUE_BULL_REDIS_HOST` / `QUEUE_BULL_REDIS_PASSWORD` — 选举和队列共用 Redis
- `QUEUE_HEALTH_CHECK_ACTIVE=true` — 启用队列健康检查
- `QUEUE_HEALTH_CHECK_INTERVAL_SECONDS=30` — 检查间隔

### 4.3 Worker 工作原理

Worker 是独立的 Node.js 进程，通过 `n8n worker` 命令启动：

- **无状态**：所有状态在 PG/Redis，worker 可任意重启
- **并发**：每个 worker 通过 `--concurrency=N` 控制同时执行的工作流数
- **拉取模式**：从 Redis BullMQ 队列拉取任务，main 推送
- **优雅关闭**：收到 SIGTERM 后停止接新任务，等待当前任务完成

---

## 5. 关键配置详解

### 5.1 必须共享的配置（多 main 一致性）

| 配置 | 说明 |
|------|------|
| `N8N_ENCRYPTION_KEY` | 凭据加密密钥，所有 main/worker 必须一致（否则凭据无法跨节点解密） |
| `DB_POSTGRESDB_*` | 共享 PostgreSQL 连接 |
| `QUEUE_BULL_REDIS_*` | 共享 Redis 连接 |
| `N8N_HOST` / `WEBHOOK_URL` | 必须指向 Traefik LB，否则 webhook 回调错乱 |

### 5.2 企业版特有配置

```env
# Multi-main 必需
EXECUTIONS_MODE=queue                    # 启用队列模式
N8N_CONCURRENCY_PRODUCTION_LIMIT=20      # main 进程并发上限
QUEUE_HEALTH_CHECK_ACTIVE=true           # 启用健康检查

# 把手动执行也路由到 worker（生产推荐）
OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true

# S3 二进制数据（需 license 激活）
N8N_DEFAULT_BINARY_DATA_MODE=s3
N8N_EXTERNAL_STORAGE_S3_HOST=minio:9000
N8N_EXTERNAL_STORAGE_S3_BUCKET_NAME=n8n-data
N8N_EXTERNAL_STORAGE_S3_FORCE_PATH_STYLE=true

# Enterprise license
N8N_LICENSE_ACTIVATION_KEY=your_key_here
```

### 5.3 Traefik 路由策略

本部署使用 file provider 定义 `n8n_cluster` 服务：

```yaml
http:
  services:
    n8n_cluster:
      loadBalancer:
        sticky:
          cookie:
            name: n8n_sid              # SSE/WebSocket 会话粘性
            httpOnly: true
            sameSite: lax
        healthCheck:
          path: /healthz
          interval: "10s"
          timeout: "3s"
        servers:
          - url: "http://n8n-main-1:5678"
          - url: "http://n8n-main-2:5678"
```

**关键点**：
- **Sticky cookie**：n8n UI 使用 SSE（Server-Sent Events）推送执行进度，必须保证同一会话路由到同一 main
- **健康检查**：故障 main 在 10s 内被剔除
- **无 weighted round-robin**：两个 main 配置相同，均匀分担

---

## 6. 性能调优

### 6.1 PostgreSQL 调优

参考配置：`config/postgres/postgresql.conf`

#### 关键参数（按 8GB 可用内存推荐）

| 参数 | 默认值 | 推荐值 | 说明 |
|------|-------|-------|------|
| `shared_buffers` | 128MB | **2GB** | 共享缓存，RAM 的 25% |
| `effective_cache_size` | 4GB | **6GB** | 查询规划器对可用缓存的估计，RAM 的 75% |
| `work_mem` | 4MB | **32MB** | 单查询排序/Hash 内存（注意：每连接 × 每操作） |
| `maintenance_work_mem` | 64MB | **512MB** | VACUUM/CREATE INDEX 内存 |
| `wal_buffers` | -1 | **16MB** | WAL 写缓冲 |
| `checkpoint_timeout` | 5min | **15min** | 检查点间隔，调大减少 IO 突发 |
| `max_wal_size` | 1GB | **4GB** | 检查点间最大 WAL |
| `random_page_cost` | 4.0 | **1.1** | SSD 接近 1.0 |
| `effective_io_concurrency` | 1 | **200** | SSD 推荐 |
| `max_connections` | 100 | **200** | main + workers + 余量 |

#### n8n 执行历史表的 VACUUM 调优

n8n 的 `execution_data`、`execution_entity` 表会高频写入。默认 autovacuum 阈值（20% 行变更）会让表膨胀严重：

```conf
autovacuum_vacuum_scale_factor = 0.05       # 5% 行变更就触发
autovacuum_analyze_scale_factor = 0.025
autovacuum_naptime = 30s                     # 检查频率
autovacuum_max_workers = 4
autovacuum_vacuum_cost_limit = 1000
```

#### 按实际硬件重新计算

```bash
# 使用 pgtune 在线工具：https://pgtune.leopard.in.ua/
# 输入：DB 版本、OS、DB 类型、总内存、CPU 核数、连接数、数据量
```

### 6.2 Redis 调优

参考配置：`config/redis/redis.conf`

| 参数 | 推荐值 | 说明 |
|------|-------|------|
| `maxmemory` | 512mb | 队列任务通常不大，512MB 足够中等规模 |
| `maxmemory-policy` | **noeviction** | 队列任务**绝对不允许**被 LRU 淘汰 |
| `appendonly` | yes | AOF 持久化 |
| `appendfsync` | everysec | 每秒刷盘，性能与可靠性平衡 |
| `save 900 1` / `save 300 10` | - | RDB 双保险 |
| `client-output-buffer-limit replica` | 64mb 16mb 60 | 防止慢客户端拖垮 |

**重要**：n8n 队列任务丢失 = 工作流执行丢失。**必须启用持久化**。

### 6.3 n8n Worker 并发调优

#### 并发数估算

每个 worker 的 `--concurrency=N` 决定同时处理多少工作流：

```
worker 总并发 = worker 数量 × 单 worker concurrency
本部署 = 3 × 10 = 30 并发
```

#### 经验公式

```
单 worker concurrency ≈ min(CPU 核数, 内存GB × 2)
```

| Worker CPU 限额 | Worker 内存 | 推荐 concurrency |
|----------------|------------|-----------------|
| 1 核 | 1 GB | 5 |
| 1.5 核 | 1.5 GB | 10 |
| 2 核 | 2 GB | 15 |
| 4 核 | 4 GB | 20 |

#### Main 并发

Main 进程的 `N8N_CONCURRENCY_PRODUCTION_LIMIT` 控制 main 自己执行工作流的上限（multi-main 模式下 main 主要负责 webhook 接收和轻量任务，建议中等值）：

```env
N8N_CONCURRENCY_PRODUCTION_LIMIT=20
```

### 6.4 资源限额（CPU/Memory）

在 `docker-compose.yml` 的 `deploy.resources.limits`：

```yaml
deploy:
  resources:
    limits:
      cpus: "2.0"        # 该容器最多用 2 核
      memory: 2g          # 该容器最多用 2GB 内存
    reservations:
      cpus: "1.0"         # Docker 至少保证 1 核可用
      memory: 1g
```

**调优建议**：
- **Main**：2 CPU / 2GB（处理 API/UI/SSE）
- **Worker**：1.5 CPU / 1.5GB（执行工作流）
- **总资源核算**：2×2 + 3×1.5 = 8.5 CPU；2×2 + 3×1.5 = 8.5GB（仅 n8n 部分）

### 6.5 Node.js 内存

n8n 是 Node.js 应用，JIT 编译后堆内存可能涨到 1-1.5GB。可通过环境变量调整：

```env
NODE_OPTIONS="--max-old-space-size=1536"   # 1.5GB 堆上限（默认约 1.5GB）
```

本部署通过 docker 内存限额间接控制，未显式设置 `NODE_OPTIONS`。

### 6.6 Traefik 调优

参考配置：`config/traefik/traefik.yml`

| 配置 | 说明 |
|------|------|
| 健康检查间隔 10s | 故障 main 10s 内剔除 |
| Sticky cookie | SSE 会话粘性 |
| 访问日志 | 默认开启，生产可关闭降低 IO |
| `entryPoints.web.http.compression` | Traefik v3 移到中间件，本部署未启用（n8n 自带 gzip） |

### 6.7 性能压测建议

部署完成后建议压测：

```bash
# 简单 webhook 压测（需先在 n8n 创建一个 webhook workflow）
hey -n 10000 -c 50 -m POST \
  -d '{"test":"data"}' \
  http://localhost:5680/webhook/your-webhook-id

# 预期指标：
# - p50 < 100ms
# - p95 < 500ms
# - 错误率 < 0.1%
```

观察 Prometheus 指标：
- `n8n_workflow_duration_seconds` — 工作流执行时长分布
- `n8n_workflow_failed_total` — 失败数
- `n8n_active_workflow_count` — 每实例活跃数

---

## 7. 监控与可观测性

### 7.1 抓取目标

Prometheus 自动抓取（见 `config/prometheus/prometheus.yml`）：

| Job | 目标 | 说明 |
|-----|------|------|
| `traefik` | traefik:8080 | LB 指标（QPS、延迟、后端健康） |
| `n8n_main_1` | n8n-main-1:5678 | n8n 主进程 #1 |
| `n8n_main_2` | n8n-main-2:5678 | n8n 主进程 #2 |
| `n8n_workers` | n8n-worker-{1,2,3}:5678 | 3 个 worker |
| `prometheus` | localhost:9090 | 自身 |

### 7.2 关键 n8n 指标

| 指标 | 含义 | 告警阈值建议 |
|------|------|-------------|
| `up` | 抓取成功 = 1 | < 1 持续 1min |
| `n8n_workflow_failed_total` | 失败总数（counter） | rate > 0 持续 5min |
| `n8n_workflow_duration_seconds` | 执行时长（histogram） | p95 > 30s |
| `n8n_active_workflow_count` | 活跃工作流数 | 趋势观察 |
| `n8n_process_cpu_usage` | n8n 进程 CPU | > 80% 持续 5min |
| `n8n_process_rss_bytes` | n8n 进程内存 | 接近限额时告警 |

### 7.3 Grafana Dashboard

自动 provisioning 的看板：`config/grafana/dashboards/n8n-ha-overview.json`

包含：
- 健康实例数
- 工作流失败率
- 工作流执行时长 p95
- 每实例活跃工作流数

访问 http://localhost:3001，凭据见 `.env`。

### 7.4 日志

```bash
# 实时查看某个 main 日志
docker compose logs -f n8n-main-1

# 实时查看所有 worker 日志
docker compose logs -f n8n-worker-1 n8n-worker-2 n8n-worker-3

# Traefik 访问日志（在容器内文件）
docker exec n8n-ha-traefik tail -f /var/log/traefik/access.log
```

调整日志级别（`.env`）：

```env
N8N_LOG_LEVEL=debug    # debug | info | warn | error
```

---

## 8. License 激活

### 8.1 获取 License

联系 n8n 销售团队：https://n8n.io/pricing/

Enterprise edition 包含：
- Multi-main mode（本部署核心）
- SAML / LDAP SSO
- External Secrets（Vault、AWS Secrets Manager）
- Log streaming（Sentry、Datadog、Syslog）
- Version Control（Git 集成）
- 高级 RBAC

### 8.2 激活步骤

**方式 A：环境变量激活（推荐）**

1. 编辑 `.env`：
   ```env
   N8N_LICENSE_ACTIVATION_KEY=你的激活码
   ```

2. 重启 main：
   ```bash
   docker compose up -d --force-recreate n8n-main-1 n8n-main-2
   ```

3. 验证：
   ```bash
   docker logs n8n-ha-main-1 2>&1 | grep -i license
   ```

**方式 B：UI 激活**

1. 访问 http://localhost:5680
2. Settings → License → 输入激活码

### 8.3 激活后启用 S3 二进制数据

```env
# 编辑 .env
N8N_BINARY_DATA_MODE=s3

# 重建所有 n8n 服务
docker compose up -d --force-recreate n8n-main-1 n8n-main-2 \
  n8n-worker-1 n8n-worker-2 n8n-worker-3
```

验证：
```bash
# 触发一个产生文件的工作流，检查 MinIO
docker exec n8n-ha-minio mc ls --recursive local/n8n-data/
```

---

## 9. 扩缩容

### 9.1 增加 Worker

**方式 A：水平扩展（推荐，3 个以内）**

直接在 `docker-compose.yml` 中复制 `n8n-worker-3` 配置，改为 `n8n-worker-4`、`n8n-worker-5`，更新 hostname、container_name、volume 路径即可。

**方式 B：垂直扩展**

调大单 worker 的 concurrency：

```yaml
n8n-worker-1:
  command: ["worker", "--concurrency=20"]   # 从 10 提到 20
  deploy:
    resources:
      limits:
        cpus: "3.0"        # 同步提升 CPU
        memory: 3g
```

### 9.2 增加 Main

Main 数量一般 2-3 个足够。添加方式：

1. 复制 `n8n-main-2` 配置为 `n8n-main-3`
2. 加入 Traefik `n8n_cluster` 的 servers 列表
3. `docker compose up -d n8n-main-3`
4. `docker compose restart traefik`

### 9.3 缩容注意事项

- **缩 worker**：直接停掉即可（worker 无状态），当前任务会重新入队
- **缩 main**：确保至少留 1 个 main；停 leader 时 follower 自动接管（5s 内）
- **不要缩到 0 main**：会导致 webhook 无法接收

---

## 10. 备份与恢复

### 10.1 备份内容

| 数据 | 位置 | 重要性 |
|------|------|-------|
| PostgreSQL | `data/postgres/` | ★★★（工作流、凭据、执行历史） |
| Redis AOF | `data/redis/` | ★★（待执行队列） |
| MinIO 二进制数据 | `data/minio/` | ★★（激活 S3 模式后） |
| n8n 配置卷 | `volumes/n8n-*/` | ★（含 license、加密元数据） |

### 10.2 备份脚本

```bash
#!/bin/bash
# backup.sh
set -e
BACKUP_DIR="./backups/$(date +%F-%H%M)"
mkdir -p "$BACKUP_DIR"

# 1. PostgreSQL（在线备份，不影响业务）
docker exec n8n-ha-postgres pg_dump -U n8n -Fc n8n_ha > "$BACKUP_DIR/postgres.dump"

# 2. Redis（触发 RDB 快照）
docker exec n8n-ha-redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning BGSAVE
sleep 5
docker cp n8n-ha-redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"
docker cp n8n-ha-redis:/data/appendonly.aof "$BACKUP_DIR/redis.aof"

# 3. MinIO bucket（激活 S3 后）
docker run --rm --network n8n-ha-net \
  -v $(pwd)/$BACKUP_DIR:/backup \
  minio/mc mirror local/n8n-data /backup/minio

echo "✅ 备份完成：$BACKUP_DIR"
```

### 10.3 恢复流程

```bash
# 1. 停止 n8n 服务（保留 PG/Redis）
docker compose stop n8n-main-1 n8n-main-2 n8n-worker-1 n8n-worker-2 n8n-worker-3

# 2. 恢复 PostgreSQL
docker exec -i n8n-ha-postgres pg_restore -U n8n -d n8n_ha -c < backups/xxx/postgres.dump

# 3. 恢复 Redis（需先停 Redis）
docker compose stop redis
docker cp backups/xxx/redis.rdb n8n-ha-redis:/data/dump.rdb
docker compose start redis

# 4. 启动 n8n
docker compose start
```

### 10.4 定时备份建议

```bash
# crontab -e
0 3 * * * cd /home/yangxiang/deployed-services/n8n-ha-enterprise && ./scripts/backup.sh
# 保留最近 30 天：find ./backups -mtime +30 -delete
```

---

## 11. 安全加固

### 11.1 网络隔离

- 所有 n8n 服务只在 `n8n-ha-net` 内通信
- 仅 Traefik 暴露外部端口（5680）
- PostgreSQL / Redis / MinIO **不要**暴露到公网（本部署为调试暴露了端口，生产应移除）

### 11.2 凭据管理

- 所有密码由 `init.sh` 生成 24 字符强随机串
- `.env` 已加入 `.gitignore`，不入版本控制
- 生产环境建议使用 Docker Secrets 或外部密钥管理（HashiCorp Vault）

### 11.3 启用 HTTPS

修改 Traefik 配置启用 TLS：

```yaml
# config/traefik/dynamic/dynamic.yml
http:
  routers:
    n8n-cluster:
      rule: "Host(`n8n.yourdomain.com`)"
      entryPoints: [websecure]
      tls:
        certResolver: letsencrypt
      service: n8n_cluster
```

同步更新 n8n 环境变量：

```env
N8N_PROTOCOL=https
N8N_HOST=n8n.yourdomain.com
WEBHOOK_URL=https://n8n.yourdomain.com/
N8N_EDITOR_BASE_URL=https://n8n.yourdomain.com/
N8N_SECURE_COOKIE=true
```

### 11.4 限制数据库访问

生产环境移除 PostgreSQL 端口映射：

```yaml
postgres:
  # ports:
  #   - "5435:5432"   # 注释掉，仅容器内访问
  networks: [n8n-ha-net]
```

---

## 12. 故障排查

### 12.1 常见问题

#### Q1: main 启动失败，日志 `ECONNREFUSED`

**原因**：依赖服务未就绪

**排查**：
```bash
docker compose ps              # 检查 PG/Redis 是否 healthy
docker logs n8n-ha-postgres    # PG 是否启动正常
docker logs n8n-ha-redis       # Redis 是否启动正常
```

**解决**：等待 `./scripts/healthcheck.sh` 全绿后再访问。

#### Q2: Worker 拉不到任务，队列空

**原因**：main 没正确推送到队列，或 worker Redis 连接异常

**排查**：
```bash
# 查看队列长度
docker exec n8n-ha-redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning LLEN bull:jobs

# 查看 worker 注册情况
docker exec n8n-ha-redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning KEYS "bull:*"
```

#### Q3: 凭据无法解密，UI 报错

**原因**：`N8N_ENCRYPTION_KEY` 在 main/worker 间不一致

**排查**：
```bash
docker exec n8n-ha-main-1 env | grep N8N_ENCRYPTION_KEY
docker exec n8n-ha-main-2 env | grep N8N_ENCRYPTION_KEY
docker exec n8n-ha-worker-1 env | grep N8N_ENCRYPTION_KEY
# 三个值必须完全相同
```

**解决**：确保所有服务都从同一 `.env` 文件读取，重建容器。

#### Q4: Webhook 404 / 回调失败

**原因**：`WEBHOOK_URL` 未指向 Traefik LB

**解决**：`.env` 中确认：
```env
WEBHOOK_URL=http://localhost:5680/
N8N_EDITOR_BASE_URL=http://localhost:5680/
```

#### Q5: Traefik 502/503

**原因**：后端 main 不健康

**排查**：
```bash
# 查看 Traefik 看到的后端健康状态
curl -s http://localhost:8889/api/http/services/n8n_cluster | \
  python3 -m json.tool

# 查看 main 健康状态
curl http://n8n-main-1:5678/healthz
curl http://n8n-main-2:5678/healthz
```

#### Q6: Redis `FATAL CONFIG FILE ERROR`

**原因**：Redis 配置文件不支持行内注释 `key value # comment`

**解决**：将注释移到独立行：
```conf
# 错误
maxmemory-policy noeviction   # 注释

# 正确
# 注释
maxmemory-policy noeviction
```

#### Q7: PostgreSQL `ECONNREFUSED 172.x.x.x:5432` 但 PG 健康

**原因**：`postgresql.conf` 未配置 `listen_addresses = '*'`，默认只监听 localhost

**解决**：在 `config/postgres/postgresql.conf` 添加 `listen_addresses = '*'`，重启 PG。

#### Q8: Prometheus `permission denied` 启动失败

**原因**：Prometheus 容器以 uid 65534 运行，宿主机数据目录权限不对

**解决**：
```bash
sudo chown -R 65534:65534 data/prometheus
```

#### Q9: Grafana `GF_PATHS_DATA is not writable`

**原因**：Grafana 容器以 uid 472 运行

**解决**：
```bash
sudo chown -R 472:472 data/grafana
```

#### Q10: Traefik docker provider 报 `client version 1.24 is too old`

**原因**：Traefik 默认使用旧版 Docker API

**解决**：在 Traefik service 加：
```yaml
environment:
  - DOCKER_API_VERSION=1.41
```

### 12.2 日志位置

| 服务 | 日志位置 |
|------|---------|
| n8n | `docker logs n8n-ha-main-1`（stdout） |
| PostgreSQL | `docker logs n8n-ha-postgres`（stdout） |
| Redis | `docker logs n8n-ha-redis`（stdout） |
| Traefik | `docker exec n8n-ha-traefik cat /var/log/traefik/traefik.log` |
| Traefik 访问日志 | `docker exec n8n-ha-traefik cat /var/log/traefik/access.log` |

---

## 13. 生产环境上线检查清单

### 13.1 配置

- [ ] `.env` 中所有密码已替换为强随机值（`init.sh` 已自动处理）
- [ ] `N8N_ENCRYPTION_KEY` 已备份到安全位置（**丢失即所有凭据无法解密**）
- [ ] `WEBHOOK_URL` 指向生产域名（非 localhost）
- [ ] Enterprise License 已激活（如使用企业特性）
- [ ] `N8N_SECURE_COOKIE=true`（启用 HTTPS 后）

### 13.2 网络

- [ ] PostgreSQL/Redis/MinIO 端口**未**暴露公网（移除 `ports:` 映射）
- [ ] 仅 Traefik 暴露 80/443
- [ ] HTTPS 配置完成，证书自动续期
- [ ] 防火墙限制管理端口（8889/9090/3001）只允许内网

### 13.3 数据

- [ ] 每日自动备份 PG，已验证可恢复
- [ ] Redis AOF + RDB 持久化开启
- [ ] 二进制数据已迁到 MinIO（激活 license 后）
- [ ] 备份保留策略已设定（如 30 天）

### 13.4 监控

- [ ] Prometheus 抓取所有 n8n 实例 + Traefik
- [ ] Grafana 看板可访问
- [ ] 关键指标告警已配置（失败率、p95 延迟、实例下线）
- [ ] 日志聚合到外部系统（ELK / Loki / CloudWatch）

### 13.5 容量

- [ ] Worker 数量 = 预期峰值 QPS × 平均工作流时长 / 单 worker concurrency
- [ ] PG `max_connections` ≥ main + worker 总数 + 50（管理/备份用）
- [ ] Redis `maxmemory` ≥ 预期队列峰值 × 2
- [ ] 磁盘剩余空间 ≥ 30 天执行历史预期大小 × 2

### 13.6 高可用验证

- [ ] 模拟 main-1 故障：`docker stop n8n-ha-main-1`，UI 仍可访问，webhook 不丢
- [ ] 模拟 worker 故障：`docker stop n8n-ha-worker-1`，工作流自动转移到 worker-2/3
- [ ] 模拟 PG 重启：`docker restart n8n-ha-postgres`，n8n 自动重连
- [ ] 模拟 Redis 重启：`docker restart n8n-ha-redis`，leader 自动重新选举

---

## 附录：参考资料

- [n8n 官方文档 - Scaling / Queue Mode](https://docs.n8n.io/hosting/scaling/queue-mode)
- [n8n 官方文档 - Multi-main setup](https://docs.n8n.io/hosting/scaling/queue-mode#multi-main-setup)
- [n8n 官方文档 - External storage (S3)](https://docs.n8n.io/hosting/scaling/external-storage)
- [n8n 官方文档 - Enterprise features](https://docs.n8n.io/enterprise)
- [Traefik v3 文档](https://doc.traefik.io/traefik/v3.1/)
- [PostgreSQL Tuning Wizard](https://pgtune.leopard.in.ua/)
- [BullMQ 文档](https://docs.bullmq.io/)

---

**文档版本**：v1.0  
**最后更新**：2026-06-22  
**部署位置**：`/home/yangxiang/deployed-services/n8n-ha-enterprise/`
