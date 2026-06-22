# n8n Enterprise HA Cluster

本地 Docker Compose 部署的 n8n 企业版高可用集群（Multi-Main Queue Mode）。

> ⚠️ Multi-main 是 n8n Self-hosted Enterprise 功能。配置按企业版标准部署；未激活 License 时实例可正常启动并运行社区版功能，激活 License 后自动启用企业版特性。

## 拓扑

```
                  ┌──────────────────┐
   Client/LB ───▶ │  traefik :5680   │
                  └────┬─────────────┘
            ┌──────────┴──────────┐
            ▼                      ▼
    ┌──────────────┐       ┌──────────────┐
    │ n8n-main-1   │       │ n8n-main-2   │   (leader / follower)
    └──────┬───────┘       └──────┬───────┘
           └──────┬────────────────┘
              ┌───▼────┐
              │ redis  │  (BullMQ + leader election)
              └───┬────┘
        ┌─────────┼──────────┐
        ▼         ▼          ▼
   worker-1  worker-2  worker-3
              │
        ┌─────▼─────┐  ┌────────┐
        │ postgres  │  │ minio  │  (binary data S3)
        └───────────┘  └────────┘

   可观测：prometheus :9090 + grafana :3001
```

## 快速开始

```bash
# 1. 初始化（生成随机密码）
./scripts/init.sh

# 2. 启动
./scripts/start.sh

# 3. 健康检查
./scripts/healthcheck.sh

# 4. 打开 http://localhost:5680 完成 n8n owner 账号注册
```

## 端口映射

| 服务 | 端口 | 凭据 |
|------|------|------|
| Traefik HTTP | 5680 | - |
| Traefik Dashboard | 8889 | - |
| PostgreSQL | 5434 | 见 .env |
| MinIO API | 9002 | 见 .env |
| MinIO Console | 9003 | 见 .env |
| Prometheus | 9090 | - |
| Grafana | 3001 | 见 .env |

## 关键配置点

- **`N8N_ENCRYPTION_KEY`** — 必须在所有 main/worker 间共享（已由 init.sh 写入 .env）
- **`N8N_LICENSE_ACTIVATION_KEY`** — 拿到企业 license 后填入 .env，重启 main 即可激活
- **`EXECUTIONS_MODE=queue`** — 启用队列模式
- **`N8N_DEFAULT_BINARY_DATA_MODE=s3`** — 二进制数据存 MinIO，避免共享卷
- **Traefik sticky cookie** — `n8n_sid`，保证 SSE/websocket 类请求会话粘性

## 性能调优要点

详见 `docs/deployment-guide.md`。核心：
1. **PostgreSQL**：`shared_buffers=2GB`、`work_mem=32MB`、autovacuum 高频小批
2. **Redis**：AOF + RDB 双持久化，`maxmemory-policy=noeviction`
3. **Worker concurrency**：每个 worker `--concurrency=10`，按 CPU 限额 1.5 核
4. **Main concurrency**：`N8N_CONCURRENCY_PRODUCTION_LIMIT=20`
5. **Traefik**：sticky session + 健康检查，故障 main 10s 内剔除

## 运维操作

```bash
./scripts/start.sh              # 启动
./scripts/stop.sh               # 停止（保留数据）
./scripts/status.sh             # 状态概览
./scripts/healthcheck.sh        # 详细健康检查
./scripts/scale-workers.sh 5    # 扩容 worker
docker compose logs -f n8n-main-1   # 查看日志
```

## License 激活

1. 获取 Enterprise license 激活码
2. 编辑 `.env`，填入 `N8N_LICENSE_ACTIVATION_KEY=你的激活码`
3. `docker compose up -d --force-recreate n8n-main-1 n8n-main-2`
4. 在 UI → Settings → License 验证激活状态

## 数据备份

```bash
# PostgreSQL
docker exec n8n-ha-postgres pg_dump -U n8n -Fc n8n_ha > backups/n8n-$(date +%F).dump

# MinIO (二进制数据)
docker run --rm --network n8n-ha-net -v $(pwd)/backups:/backup \
  minio/mc mirror local/n8n-data /backup/minio-$(date +%F)
```

## 故障排查

| 现象 | 排查 |
|------|------|
| main 启动失败 | `docker compose logs n8n-main-1`，检查 PG/Redis 连接 |
| Worker 拉不到任务 | 检查 Redis 队列键 `bull:*`，确认 main 推送 |
| 凭据无法解密 | 确认所有实例的 `N8N_ENCRYPTION_KEY` 一致 |
| Webhook 404 | 确认 `WEBHOOK_URL` 指向 Traefik LB（5680） |
| Traefik 5xx | 检查 `traefik.http.services.*.loadbalancer.healthcheck` |

## 完整文档

部署、调优、扩展指南：`docs/deployment-guide.md`
