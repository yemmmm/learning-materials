# n8n Enterprise HA Cluster

> Changed: 2026-06-25 - 全面重构，参考官方 n8n-hosting (withPostgresAndWorker)

基于 Docker Compose 的 n8n 企业版高可用集群（Queue Mode），支持多服务器部署。

> **参考**: https://github.com/n8n-io/n8n-hosting/tree/main/docker-compose/withPostgresAndWorker

## 架构

```
                        ┌──────────────────────┐
 Client / Webhook ───▶  │ Traefik (:80/:443)   │
                        └──────────┬───────────┘
                                   │ sticky cookie + healthcheck
                                   ▼
                        ┌──────────────────────┐
                        │ n8n-main-{1,2}       │  ← API / UI / Webhook
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

副服务器可运行多个 worker 实例以增加任务执行吞吐量。

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
docker compose -f docker-compose.worker.yml up -d

# 5. 启动显式成对的 worker/runner
docker compose -f docker-compose.worker.yml up -d n8n-worker-1 n8n-worker-1-runner n8n-worker-2 n8n-worker-2-runner
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
docker compose logs -f n8n-main-1 n8n-main-2      # 查看 n8n main 日志
docker compose logs -f n8n-worker-1 n8n-worker-2  # 查看 worker 日志
```

## License 激活

1. 获取 Enterprise license 激活码
2. 编辑 `.env`，填入 `N8N_LICENSE_ACTIVATION_KEY=你的激活码`
3. `docker compose up -d --force-recreate n8n-main-1 n8n-main-2 n8n-worker-1 n8n-worker-2`
4. 在 UI → Settings → License 验证激活状态

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
| n8n 启动失败 | `docker compose logs n8n`，检查 PG/Redis 连接 |
| Worker 拉不到任务 | 检查 Redis 队列键 `bull:*` |
| 凭据无法解密 | 确认所有实例的 `N8N_ENCRYPTION_KEY` 一致 |
| Webhook 404 | 确认 `WEBHOOK_URL` 指向 Traefik LB |
| Code 节点执行失败 | 检查 task runner 是否运行: `docker compose logs n8n-main-1-runner n8n-worker-1-runner` |
| Binary data 读取失败 | 检查 MinIO、bucket 和 `N8N_EXTERNAL_STORAGE_S3_*` 配置 |
| 副服务器连接不上 Redis | 确认主服务器防火墙放行 6379 端口 |
