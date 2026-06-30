# n8n Enterprise HA Cluster

> Changed: 2026-06-25 - 全面重构，参考官方 n8n-hosting (withPostgresAndWorker)

基于 Docker Compose 的 n8n 企业版高可用集群（Queue Mode），支持多服务器部署。

> **参考**: https://github.com/n8n-io/n8n-hosting/tree/main/docker-compose/withPostgresAndWorker

## 架构

> 团队分享会讲解稿见 [docs/internal-sharing-notes.md](./docs/internal-sharing-notes.md)。

```
                        ┌──────────────────────┐
 Client / Webhook ───▶  │ Traefik (:80/:443)   │
                        └──────────┬───────────┘
                                   │ sticky cookie + healthcheck
                                   ▼
                        ┌──────────────────────┐
                        │ n8n-main-{1,2}       │  ← API / UI / Webhook（激活后可扩到 3+）
                        │ + main runners       │  ← Code 节点 sidecar
                        └──────────┬───────────┘
                                   │ push job
                                   ▼
                        ┌──────────────────────┐
                        │ Redis :6379          │  ← BullMQ + Leader Election
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │ n8n-worker-{1,2}     │  ← 任务执行器，可横向扩展
                        │ + worker runners     │  ← Code 节点 sidecar
                        └──────────────────────┘

   外部 PostgreSQL ←── 所有 n8n 实例共享
   MinIO / S3      ←── 二进制数据共享存储
```

## 多服务器部署

| 服务器 | 主机名 | Compose 文件 | 角色 |
|--------|--------|-------------|------|
| 主 (11vm) | li19dksfai11vm.bmwgroup.net | docker-compose.yml | Traefik + Redis + MinIO + 2 main + 2 worker + runners |
| 副 (10vm) | li19dksfai10vm.bmwgroup.net | docker-compose.worker.yml | 2 worker + 2 runner（横向扩展执行能力） |

副服务器可运行多个 worker 实例以增加任务执行吞吐量。worker 横向扩展不依赖 Enterprise license；Enterprise license 主要影响 multi-main 高可用和 S3 external binary data 等企业能力。

## 快速开始

### 主服务器 (11vm)

```bash
# 1. 初始化（自动生成密码）
./scripts/init.sh

# 2. 编辑 .env，填写外部 PostgreSQL 连接信息
vim .env

# 3. 启动
./scripts/start.sh

# 4. 健康检查
./scripts/healthcheck.sh

# 5. 访问 https://li19dksfai11vm.bmwgroup.net 完成 owner 注册
```

### 副服务器 (10vm)

```bash
# 1. 将文件复制到副服务器: docker-compose.worker.yml + .env + config/redis/
# 2. 修改 .env 中的 QUEUE_BULL_REDIS_HOST 指向主服务器
# 3. 修改 .env 中的 N8N_EXTERNAL_STORAGE_S3_HOST 指向主服务器 MinIO:
#    http://li19dksfai11vm.bmwgroup.net:9000
# 3. 确认 N8N_ENCRYPTION_KEY 和 RUNNERS_AUTH_TOKEN 与主服务器一致
# 4. 启动
docker-compose -f docker-compose.worker.yml up -d

# 5. 启动显式成对的 worker/runner
docker-compose -f docker-compose.worker.yml up -d n8n-worker-1 n8n-worker-1-runner n8n-worker-2 n8n-worker-2-runner
```

## 端口映射

| 服务 | 端口 | 说明 |
|------|------|------|
| Traefik HTTP | 80 | 自动重定向到 HTTPS |
| Traefik HTTPS | 443 | n8n UI/API |
| Traefik Dashboard | 8889 (127.0.0.1) | 仅本机访问 |
| Redis | 6379 | 供副服务器连接 |
| MinIO API | 9000 | 供 n8n / 副服务器 worker 访问 S3 binary data |
| MinIO Console | 9001 (127.0.0.1) | 仅本机访问 |

## 关键配置

- **`N8N_ENCRYPTION_KEY`** — 所有实例必须一致（init.sh 自动生成）
- **`RUNNERS_AUTH_TOKEN`** — 所有实例必须一致（init.sh 自动生成）
- **`N8N_LICENSE_ACTIVATION_KEY`** — 企业 License，在 .env 中配置
- **`N8N_MULTI_MAIN_SETUP_ENABLED=true`** — 激活 Enterprise 后启用 multi-main，所有 main 必须一致
- **`N8N_MULTI_MAIN_SETUP_KEY_TTL=10`** — multi-main leader key TTL，通常保持默认即可
- **`N8N_MULTI_MAIN_SETUP_CHECK_INTERVAL=3`** — leader 检查间隔，通常保持默认即可
- **外部 PostgreSQL** — 需手动填写 DB_POSTGRESDB_* 连接信息
- **Task Runners** — n8n 2.0+ Code 节点必需，每个 n8n 实例配一个 sidecar
- **MinIO / S3** — Queue Mode 下用于跨 main/worker 共享二进制数据

## 运维操作

```bash
./scripts/start.sh              # 启动
./scripts/stop.sh               # 停止（保留数据）
./scripts/status.sh             # 状态概览
./scripts/healthcheck.sh        # 详细健康检查
./scripts/scale-workers.sh 2    # 启动两组 worker + runner（主服务器）
docker-compose logs -f n8n-main-1 n8n-main-2      # 查看 n8n main 日志
docker-compose logs -f n8n-worker-1 n8n-worker-2  # 查看 worker 日志
```

## License 激活

### 激活前后架构差异

| 能力 | 未激活 | 激活后 |
|------|--------|--------|
| 单 main + Redis queue | 支持 | 支持 |
| worker 横向扩展 | 支持 | 支持 |
| worker `--concurrency` 调整 | 支持 | 支持 |
| 多服务器 worker | 支持，需共享 PG/Redis/`N8N_ENCRYPTION_KEY` | 支持 |
| multi-main 高可用 | 不应作为生产能力依赖 | 支持 |
| main 数量 | 建议只运行 1 个对外 main | 可运行 2 个或更多 main |
| leader/follower 选举 | 不应依赖 | 支持 |
| S3 external binary data | 不建议依赖，使用 filesystem | 支持 |
| SSO/RBAC/Git/External Secrets/Log streaming | 不支持 | 支持 |

未激活时推荐拓扑：

```text
Traefik -> n8n-main-1 -> Redis queue -> n8n-worker-1/2/N
                         |
                      PostgreSQL
```

激活后目标拓扑：

```text
Traefik -> n8n-main-1/2/N -> Redis queue -> n8n-worker-1/2/N
            leader/follower |
                         PostgreSQL + MinIO/S3
```

### main 与 worker 扩展边界

worker 是执行面，从 Redis 队列拉取 execution job 后执行，天然可以通过增加 worker 数量或调整 `--concurrency` 扩展吞吐，不依赖 Enterprise license。

main 是控制面，负责 UI/API/webhook、任务入队、active workflow 管理，以及定时触发、轮询触发、持久连接、执行清理等 at-most-once 任务。多个 main 不能像 worker 一样简单复制后直接并行，否则可能出现同一触发器重复执行、后台任务重复运行或入口状态不一致。Enterprise multi-main 通过 leader/follower 机制让多个 main 协调这些全局唯一任务。

激活后 main 不是只能 2 个。当前方案默认部署 `n8n-main-1` 和 `n8n-main-2`，只是初始冗余配置；需要更多入口容量时，可以继续增加 `n8n-main-3`、`n8n-main-4`。新增 main 时必须同步：

- 复制一个 main 服务定义，使用唯一 `container_name`、`hostname` 和独立 `/home/node/.n8n` 数据目录
- 为新增 main 增加对应 runner sidecar
- 在 `config/traefik/dynamic/dynamic.yml` 的 `n8n_cluster` 后端加入新 main 地址
- 保持所有 main 连接同一个 PostgreSQL、Redis，使用同一个 `N8N_ENCRYPTION_KEY`
- 保持所有 main/worker 使用同一个 n8n 版本

### 激活步骤

1. 获取 Enterprise license 激活码
2. 编辑 `.env`，填入：
   ```env
   N8N_LICENSE_ACTIVATION_KEY=你的激活码
   N8N_MULTI_MAIN_SETUP_ENABLED=true
   N8N_MULTI_MAIN_SETUP_KEY_TTL=10
   N8N_MULTI_MAIN_SETUP_CHECK_INTERVAL=3
   ```
3. 首次激活建议先重建一个 main，确认 license 初始化成功：
   ```bash
   docker-compose up -d --force-recreate n8n-main-1
   docker-compose logs -f n8n-main-1 | grep -i license
   ```
4. 再重建其他 main/worker：
   ```bash
   docker-compose up -d --force-recreate n8n-main-2 n8n-worker-1 n8n-worker-2
   ```
5. 在 UI → Settings → License 验证激活状态

### 激活后启用 S3 binary data

激活前如果暂不使用 Enterprise S3 external storage，建议在 `.env` 明确使用 filesystem：

```env
N8N_AVAILABLE_BINARY_DATA_MODES=filesystem
N8N_DEFAULT_BINARY_DATA_MODE=filesystem
```

激活后再切换为 S3：

```env
N8N_AVAILABLE_BINARY_DATA_MODES=filesystem,s3
N8N_DEFAULT_BINARY_DATA_MODE=s3
```

## 数据备份

```bash
# PostgreSQL（外部，使用 pg_dump 备份）
pg_dump -h <PG_HOST> -U <PG_USER> -Fc <PG_DATABASE> > backup-$(date +%F).dump

# Redis 数据
cp -r data/redis backup/redis-$(date +%F)/
```

## 故障排查

| 现象 | 排查 |
|------|------|
| n8n 启动失败 | `docker-compose logs n8n`，检查 PG/Redis 连接 |
| Worker 拉不到任务 | 检查 Redis 队列键 `bull:*` |
| 凭据无法解密 | 确认所有实例的 `N8N_ENCRYPTION_KEY` 一致 |
| Webhook 404 | 确认 `WEBHOOK_URL` 指向 Traefik LB |
| Code 节点执行失败 | 检查 task runner 是否运行: `docker-compose logs n8n-main-1-runner n8n-worker-1-runner` |
| Binary data 读取失败 | 检查 MinIO、bucket 和 `N8N_EXTERNAL_STORAGE_S3_*` 配置 |
| 副服务器连接不上 Redis | 确认主服务器防火墙放行 6379 端口 |
