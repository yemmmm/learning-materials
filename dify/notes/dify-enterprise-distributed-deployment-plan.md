# Dify 企业版分布式部署方案

> 适用版本：Dify Enterprise 0.14.4 (3.7.5)
> 部署日期：2026-06-05
> 当前环境：单机 Docker Compose → 目标：多机分布式

---

## 一、背景与目标

### 1.1 现状

当前 Dify 企业版运行在单台服务器上（`192.168.5.25`），所有服务通过 Docker Compose 部署，资源占用已满但性能指标未达预期。

### 1.2 目标

- 将计算密集型服务（api、worker）扩展到多台服务器
- 保持共享基础设施（PostgreSQL、Redis）的高可用性
- **关键约束：cluster-id 不能变化，确保企业版 license 持续有效**

---

## 二、Cluster-ID 机制分析

### 2.1 生成原理

Dify 企业版的 cluster-id 由 `/app/clusterid` 二进制程序生成：

```
cluster-id = SHA256(/sys/class/dmi/id/product_uuid)
```

当前服务器：
- Product UUID: `03000200-0400-0500-0006-000700080009`
- Cluster ID: `8c2fa12a04068a92d52764893d07439fe17ca2bd8e6d6a521c35519b818d7445`
- Mode: `Standalone`

### 2.2 License 绑定关系

```
服务器产品UUID ──→ clusterid 二进制 ──→ Cluster ID ──→ License Server (licenses.dify.ai)
                                                              │
                                                     enterprise.licenses 表
```

### 2.3 换机影响

| 操作 | cluster-id | License |
|------|-----------|---------|
| 在原机器上扩展 api/worker | 不变 | ✅ 有效 |
| 迁移 PostgreSQL 到独立服务器 | 不变 | ✅ 有效 |
| **迁移 dify-enterprise 到新物理机** | **改变** | ❌ 失效 |
| **全新服务器部署全部服务** | **改变** | ❌ 失效 |

### 2.4 应对策略

- **首选**：dify-enterprise 服务保留在原（已激活的）服务器上
- **备选**：如需整体迁移，联系 Dify 官方重新签发 license

---

## 三、架构设计

### 3.1 整体架构图

```
                        ┌─────────────────────────────────┐
                        │       Load Balancer / 反向代理     │
                        │     (Nginx / HAProxy / Caddy)     │
                        │         Port 80 / 443             │
                        └──────┬──────────────┬─────────────┘
                               │              │
              ┌────────────────┼──────┐  ┌────┴────────────────┐
              │     Server A (原)      │  │  Server B (新增)     │
              │   192.168.5.25         │  │  192.168.5.26        │
              │                       │  │                      │
              │  ★ dify-enterprise    │  │  • api (副本)        │
              │    (cluster-id 绑定)   │  │  • worker (副本)     │
              │  ★ db_postgres        │  │  • web               │
              │  ★ redis              │  │  • sandbox           │
              │  ★ worker_beat        │  │  • ssrf_proxy        │
              │  • api (主)           │  │  • plugin_daemon     │
              │  • worker (主)        │  │                      │
              │  • web                │  └──────────────────────┘
              │  • dify-enterprise-   │
              │    frontend           │
              │  • dify-plugin-manager│
              │  • dify-audit         │
              │  • dify-gateway       │
              │  • weaviate           │
              │  • sandbox            │
              │  • ssrf_proxy         │
              │  • plugin_daemon      │
              └───────────────────────┘
```

### 3.2 网络拓扑

```
                         ┌──────────────┐
                         │   互联网 / 用户  │
                         └──────┬───────┘
                                │
                         ┌──────┴───────┐
                         │  LB / 反向代理 │          Server A
                         │  (端口 80/443) │─────── 192.168.5.25
                         └──────┬───────┘      │
                                │              ├── dify-gateway (Caddy)
                    ┌───────────┼───────────┐  ├── dify-enterprise :8082
                    │           │           │  ├── api :5001
              ┌─────┴─────┐ ┌──┴────┐ ┌────┴─────┐  ├── worker
              │ Server A  │ │Server │ │ Server N │  ├── web :3000
              │ (核心服务) │ │  B    │ │  (扩展)  │  ├── db_postgres :5432
              └───────────┘ └───────┘ └──────────┘  ├── redis :6379
                    │           │           │       ├── weaviate :8080
                    └───────────┼───────────┘       ├── sandbox :8194
                                │                   ├── plugin_daemon :5002
              ┌─────────────────┴─────────────┐     ├── dify-audit :8083
              │     共享基础设施网络              │     ├── dify-plugin-manager :8084
              │  PostgreSQL │ Redis │ Weaviate │     └── worker_beat
              │  (全部指向 Server A)            │
              └───────────────────────────────┘
```

### 3.3 服务分层表

| 层级 | 服务 | 可水平扩展 | 单实例要求 | 部署位置 | 备注 |
|------|------|-----------|-----------|---------|------|
| 网关层 | dify-gateway (Caddy) | 可 | 否 | Server A | 可用外部 LB 替代 |
| 网关层 | dify-enterprise-frontend | 可 | 否 | Server A | 企业管理后台 UI |
| 核心层 | **dify-enterprise** | 否 | **是** | **Server A（必须）** | **cluster-id 绑定** |
| 核心层 | api | **是** | 否 | Server A + B + N | Flask/gunicorn 工作负载 |
| 核心层 | web | 可 | 否 | 任意 | Next.js 前端 |
| 任务层 | worker | **是** | 否 | Server A + B + N | Celery 异步任务 |
| 任务层 | **worker_beat** | 否 | **是（全局唯一）** | Server A | Celery Beat 调度 |
| 任务层 | sandbox | 可 | 否 | 任意 | 代码执行沙箱 |
| 中间件层 | **db_postgres** | 否 | **是** | Server A（或独立） | 主数据库 |
| 中间件层 | **redis** | 可(Sentinel) | 否 | Server A（或独立） | 缓存 + Celery Broker |
| 中间件层 | ssrf_proxy | 可(每节点) | 否 | 每台有 sandbox 的节点 | SSRF 防护 |
| 向量层 | weaviate | 可 | 否 | 独立或 Server A | 向量数据库 |
| 插件层 | plugin_daemon | 可(注意存储) | 否 | 任意 | 需要共享存储 |
| 企业层 | dify-plugin-manager | 可 | 否 | Server A | 插件市场 |
| 企业层 | dify-audit | 可 | 否 | Server A | 审计日志 |

---

## 四、数据流说明

### 4.1 请求路由

```
用户 → 反向代理 (LB)
  ├── /                    → web:3000 (任一节点)
  ├── /console/api/*       → api:5001 (任一节点)
  ├── /v1/*                → api:5001 (任一节点)
  ├── /v1/dashboard/*      → dify-enterprise:8082 (Server A)
  ├── /admin-api/*         → dify-enterprise:8082 (Server A)
  ├── /v1/plugin-manager/* → dify-plugin-manager:8084 (Server A)
  ├── /v1/audit/*          → dify-audit:8083 (Server A)
  ├── /scim/*              → dify-enterprise:8082 (Server A)
  └── /e/{hook_id}         → plugin_daemon:5002
```

### 4.2 Celery 任务流

```
                              ┌──────────────────┐
API ──→ Redis (Broker) ──→    │   Celery Workers  │
                              │  Server A worker   │
                              │  Server B worker   │
                              │  Server N worker   │
                              └───────┬────────────┘
                                      │
                              ┌───────┴────────────┐
                              │  Redis (Backend)    │
                              │  PostgreSQL (结果)  │
                              └────────────────────┘

Worker Beat (仅 Server A) ──→ Redis (调度) ──→ Workers 执行
```

### 4.3 数据库连接流

```
Server A  api ──→ db_postgres:5432 (本地, pool_size=20)
Server B  api ──→ db_postgres:5432 (远程, pool_size=20)
Server N  api ──→ db_postgres:5432 (远程, pool_size=20)
                         │
                  POSTGRES_MAX_CONNECTIONS=300
```

---

## 五、详细部署步骤

### 5.1 前置准备

#### 服务器规划

| 角色 | IP | 配置建议 | 职责 |
|------|-----|---------|------|
| Server A（原） | 192.168.5.25 | 4C8G+ | 核心服务 + 数据库 + 缓存 |
| Server B（新） | 192.168.5.26 | 4C8G+ | 计算节点（api + worker） |
| Server N（新） | 192.168.5.x | 4C8G+ | 可选扩展节点 |

> **网络要求**：所有节点必须在同一内网（延迟 < 1ms），建议同 VPC/同交换机。

#### 防火墙规则

```bash
# Server A 需要对外开放
5432  → PostgreSQL (仅限 Server B/N)
6379  → Redis       (仅限 Server B/N)
80/443 → 主入口
# Server B/N 只需开放 80/443 给 LB
```

### 5.2 Server A 配置（原服务器）

#### 5.2.1 修改 PostgreSQL 配置

```bash
# .env 调整
POSTGRES_MAX_CONNECTIONS=300      # 从 100 提升
POSTGRES_SHARED_BUFFERS=256MB     # 按内存 25% 调整
POSTGRES_EFFECTIVE_CACHE_SIZE=8196MB

# 开放远程访问 - 编辑 volumes/db/data/pgdata/pg_hba.conf
# 添加行:
host    all             all             192.168.5.0/24          md5
```

#### 5.2.2 修改 Redis 配置

```bash
# .env 调整
# 确保 Redis 监听所有接口（默认已配置）
REDIS_HOST=redis    # 保持容器内服务名不变
REDIS_PASSWORD=difyai123456

# 远程节点通过 192.168.5.25:6379 访问（需开放端口或通过 Docker 网络）
```

#### 5.2.3 精简 docker-compose.yaml（Server A）

在 Server A 上只保留以下服务：

```yaml
# Server A 的 docker-compose 保留:
services:
  dify-enterprise        # 保留（核心 license 绑定）
  db_postgres            # 保留（共享数据库）
  redis                  # 保留（共享缓存）
  worker_beat            # 保留（唯一调度器）
  dify-gateway           # 保留（网关）
  dify-enterprise-frontend # 保留
  dify-plugin-manager    # 保留
  dify-audit             # 保留
  weaviate               # 保留（或独立部署）
  plugin_daemon          # 保留
  # api, worker, web, sandbox, ssrf_proxy 移到扩展节点
```

#### 5.2.4 暴露必要端口

```yaml
# docker-compose.yaml 修改
db_postgres:
  ports:
    - "5432:5432"      # 允许远程访问（注意安全组限制）

redis:
  ports:
    - "6379:6379"      # 允许远程访问（注意安全组限制）
```

### 5.3 Server B/N 配置（新节点）

#### 5.3.1 创建精简的 docker-compose.yaml

```yaml
# Server B 的 docker-compose.yaml
version: '3.8'

services:
  api:
    image: langgenius/dify-api:3d2aea11a
    restart: always
    environment:
      MODE: api
      # ---- 数据库连接 ----
      DB_HOST: 192.168.5.25
      DB_PORT: 5432
      DB_USERNAME: postgres
      DB_PASSWORD: difyai123456
      DB_DATABASE: dify
      DB_TYPE: postgresql
      SQLALCHEMY_POOL_SIZE: 20
      SQLALCHEMY_MAX_OVERFLOW: 10
      # ---- Redis 连接 ----
      REDIS_HOST: 192.168.5.25
      REDIS_PORT: 6379
      REDIS_PASSWORD: difyai123456
      # ---- Celery ----
      CELERY_BROKER_URL: redis://:difyai123456@192.168.5.25:6379/1
      # ---- 其他配置 ----
      SECRET_KEY: your-secret-key-here-replace-with-actual-value
      CONSOLE_API_URL: http://192.168.5.25
      CONSOLE_WEB_URL: http://192.168.5.25
      SERVICE_API_URL: http://192.168.5.25
      APP_API_URL: http://192.168.5.25
      APP_WEB_URL: http://192.168.5.25
      FILES_URL: http://192.168.5.25
      STORAGE_TYPE: local
      STORAGE_LOCAL_PATH: storage
      # ... 其余环境变量与 Server A 相同
    volumes:
      - ./volumes/app/storage:/app/api/storage
    depends_on: []   # 不依赖本地 DB/Redis

  worker:
    image: langgenius/dify-api:3d2aea11a
    restart: always
    environment:
      MODE: worker
      # ---- 与 api 相同的数据库/Redis 配置 ----
      DB_HOST: 192.168.5.25
      # ... (同上)
    depends_on: []

  web:
    image: langgenius/dify-web:3d2aea11a
    restart: always
    environment:
      CONSOLE_API_URL: http://192.168.5.25
      APP_API_URL: http://192.168.5.25
      NEXT_PUBLIC_COOKIE_DOMAIN: ''
    depends_on: []

  sandbox:
    image: langgenius/dify-sandbox:0.2.12
    restart: always
    environment:
      SANDBOX_API_KEY: dify-sandbox
      SANDBOX_GIN_MODE: release

  ssrf_proxy:
    image: ubuntu/squid:latest
    restart: always
    volumes:
      - ./ssrf_proxy/squid.conf:/etc/squid/squid.conf:ro
```

#### 5.3.2 配置共享存储（重要）

```bash
# 方案A: NFS 共享存储
# Server A 上设置 NFS 服务端
sudo apt install nfs-kernel-server
sudo mkdir -p /data/dify-storage
echo "/data/dify-storage 192.168.5.0/24(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports
sudo exportfs -ra

# Server B/N 上挂载
sudo apt install nfs-common
sudo mount -t nfs 192.168.5.25:/data/dify-storage /mnt/dify-storage

# 方案B: S3 兼容存储（推荐生产环境）
# 在 .env 中配置：
STORAGE_TYPE=s3
S3_ENDPOINT=https://s3.your-region.amazonaws.com
S3_BUCKET_NAME=dify-files
S3_ACCESS_KEY=xxx
S3_SECRET_KEY=xxx
```

### 5.4 负载均衡配置

```nginx
# /etc/nginx/nginx.conf (LB 服务器)
upstream dify_api {
    least_conn;
    server 192.168.5.25:5001 max_fails=3 fail_timeout=30s;
    server 192.168.5.26:5001 max_fails=3 fail_timeout=30s;
    # server 192.168.5.27:5001 max_fails=3 fail_timeout=30s;
}

upstream dify_web {
    least_conn;
    server 192.168.5.25:3000 max_fails=3 fail_timeout=30s;
    server 192.168.5.26:3000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name dify.your-domain.com;

    # Web 前端
    location / {
        proxy_pass http://dify_web;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # Console API
    location /console/api/ {
        proxy_pass http://dify_api;
        proxy_read_timeout 3600s;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Service API
    location /v1/ {
        proxy_pass http://dify_api;
        proxy_read_timeout 3600s;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 企业 API（强制路由到 Server A）
    location /admin-api/ {
        proxy_pass http://192.168.5.25:80;
    }
    location /v1/dashboard/ {
        proxy_pass http://192.168.5.25:80;
    }
    location /scim/ {
        proxy_pass http://192.168.5.25:80;
    }
}
```

### 5.5 启动顺序

```bash
# 1. 先在 Server A 启动核心服务
cd /path/to/dify-enterprise-0325
docker compose up -d db_postgres redis  # 先启动基础设施
docker compose up -d                      # 启动其余核心服务

# 2. 验证 Server A 正常运行
curl http://192.168.5.25:5001/health
curl http://192.168.5.25:8082/health

# 3. 在 Server B/N 启动扩展服务
cd /path/to/dify-worker-node
docker compose up -d

# 4. 启动/更新负载均衡器
sudo systemctl reload nginx
```

---

## 六、关键配置验证清单

### 6.1 连通性验证

```bash
# 从 Server B 测试到 Server A 的连通性
# PostgreSQL
psql -h 192.168.5.25 -U postgres -d dify -c "SELECT 1;"

# Redis
redis-cli -h 192.168.5.25 -a difyai123456 PING

# API
curl http://192.168.5.25:5001/health

# Enterprise
curl http://192.168.5.25:8082/health
```

### 6.2 License 验证

```bash
# 在 Server A 上验证 cluster-id 不变
docker exec <enterprise-container> /app/clusterid

# 验证企业 API 可达
curl http://192.168.5.25/admin-api/v1/workspaces

# 如果返回 403 "License is invalid"，说明 license 已经失效
# 预期返回正常数据
```

### 6.3 Worker 验证

```bash
# 查看 Celery worker 状态
docker exec <api-container> celery -A celery_entrypoint.celery inspect active_queues

# 确认 worker_beat 只有一个在运行
docker exec <worker_beat-container> ps aux | grep beat
```

---

## 七、性能调优参数

### 7.1 API 服务

```bash
# gunicorn workers 数量（每个 API 实例）
SERVER_WORKER_AMOUNT=4           # CPU 核数 × 2 + 1
SERVER_WORKER_CLASS=gevent
SERVER_WORKER_CONNECTIONS=20     # 从 10 提高
GUNICORN_TIMEOUT=360
```

### 7.2 Celery Worker

```bash
CELERY_WORKER_AMOUNT=4           # 每个 worker 实例的并发数
# 或者使用自动伸缩：
CELERY_AUTO_SCALE=true
CELERY_MAX_WORKERS=10
CELERY_MIN_WORKERS=2
```

### 7.3 数据库连接池

```bash
# Server A（有本地 api）
SQLALCHEMY_POOL_SIZE=20
POSTGRES_MAX_CONNECTIONS=300

# Server B（仅远程访问）
SQLALCHEMY_POOL_SIZE=15
# 总连接数估算: (20 + 15 + 15) × 2(overflow) + 10(enterprise) ≈ 110
# 远小于 300，安全
```

### 7.4 Redis

```bash
# 增加连接池
REDIS_DB=0
# Celery broker 使用独立 DB
CELERY_BROKER_URL=redis://:difyai123456@192.168.5.25:6379/1
```

---

## 八、监控要点

### 8.1 关键指标

| 指标 | 监控来源 | 告警阈值 |
|------|---------|---------|
| API 延迟 P99 | LB 日志 | > 2s |
| Worker 队列长度 | Redis `LLEN` | > 1000 |
| DB 连接数 | `pg_stat_activity` | > 200 |
| Redis 内存使用 | `INFO memory` | > 80% |
| cluster-id 一致性 | 定期检查 | 任何变化 |
| enterprise API 可达性 | HTTP probe | 非 200 |

### 8.2 日志聚合

```bash
# 所有节点配置统一的日志输出
LOG_LEVEL=INFO
LOG_FILE=/app/logs/server.log
# 推荐使用 OTLP 收集器或 Filebeat 统一收集
```

---

## 九、常见问题与解决方案

### Q1: 如何确认当前 cluster-id？

```bash
docker exec $(docker ps --filter "ancestor=langgenius/dify-enterprise:0.14.4" -q) /app/clusterid
```

### Q2: 分布式后 License 失效怎么办？

1. 确认 dify-enterprise 是否仍在原服务器运行
2. 确认 enterprise 数据库的 licenses 表数据完整
3. 联系 Dify 技术支持重新签发 license

### Q3: Worker 任务调度冲突怎么办？

```bash
# 确保 worker_beat 只有一个实例
docker ps | grep worker_beat   # 应该只有 1 个

# 如果多个 beat 同时运行，会重复调度定时任务
# 立即停止多余的 beat 实例
```

### Q4: 文件上传后其他节点访问不到？

```bash
# 确保共享存储配置正确
# 检查所有节点的 FILES_URL 和 STORAGE_TYPE
# 生产环境建议使用 S3 兼容存储，避免 NFS 瓶颈
```

### Q5: 数据库连接池耗尽？

```bash
# 递减调整每个节点的 POOL_SIZE
# 监控 PostgreSQL 活跃连接数
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
```

---

## 十、迁移回滚方案

如果分布式部署后出现问题：

```bash
# 快速回滚到单机模式
# 1. 停止 Server B/N 上的扩展服务
ssh server-b "docker compose down"
ssh server-n "docker compose down"

# 2. 在 Server A 恢复完整 docker-compose
cd /path/to/dify-enterprise-0325
docker compose up -d

# 3. 恢复 LB 配置指回单机
sudo nginx -t && sudo systemctl reload nginx

# 总回滚时间：< 5 分钟
```

---

## 十一、总结

| 维度 | 结论 |
|------|------|
| 可行性 | ✅ 完全可行 |
| 核心约束 | dify-enterprise 必须留在原服务器（cluster-id 绑定） |
| 扩展收益 | api/worker 水平扩展可线性提升吞吐量 |
| 主要风险 | 网络延迟、共享存储瓶颈、连接池耗尽 |
| 推荐策略 | 先扩展 2 台计算节点，观察效果再决定是否继续扩展 |
| 备份方案 | 可随时回滚到单机模式 |
