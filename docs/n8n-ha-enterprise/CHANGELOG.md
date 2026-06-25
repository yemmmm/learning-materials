# 变更日志

## [未发布]

### 新增
- 2026-06-25: **全面重构** - 参考官方 n8n-hosting (withPostgresAndWorker) 重新编写部署架构
  - 采用 YAML Anchors (`&shared`, `&runner`) 消除配置重复
  - 引入 Task Runner sidecar 容器（n8n 2.0+ Code 节点必需）
  - 新增 `docker-compose.worker.yml` 支持副服务器 (10vm) 横向扩展
  - 外部 PostgreSQL 支持（移除容器化 PG，由外部管理）

### 删除
- 2026-06-25: 移除 PostgreSQL 容器服务（改用外部 PG）
- 2026-06-25: 移除 MinIO 容器服务（简化架构，需要时再添加 S3 配置）
- 2026-06-25: 移除 Prometheus + Grafana 监控服务（后续版本单独部署）
- 2026-06-25: 移除 config/postgres/、config/prometheus/、config/grafana/ 目录

### 变更
- 2026-06-25: docker-compose.yml 从 11 容器简化为 7 容器 (Traefik + Redis + n8n + runner + worker + worker-runner)
- 2026-06-25: .env.example 重构 - 移除 MinIO/Grafana 变量，新增外部 PG 连接变量、RUNNERS_AUTH_TOKEN
- 2026-06-25: Traefik 配置简化 - 移除 Grafana 子路径路由、Prometheus metrics，增加 HTTP→HTTPS 自动重定向
- 2026-06-25: Redis 配置移除硬编码密码，密码通过 .env 中的 QUEUE_BULL_REDIS_PASSWORD 传入
- 2026-06-25: 所有数据路径改为挂载到 compose 文件同目录下 (`./data/...`)
- 2026-06-25: 所有脚本全面重构，适配新架构
- 2026-06-25: CLAUDE.md 更新架构说明和关键配置规则

### 多服务器部署架构
- **主服务器 (11vm)**: docker-compose.yml → Traefik + Redis + n8n + worker + runners
- **副服务器 (10vm)**: docker-compose.worker.yml → worker + runner（连接主服务器 Redis）
- 共享组件: 外部 PostgreSQL（需手动配置连接信息）
- 关键约束: N8N_ENCRYPTION_KEY 和 RUNNERS_AUTH_TOKEN 必须在所有服务器上保持一致
