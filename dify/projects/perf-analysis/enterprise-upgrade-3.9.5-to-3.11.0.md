# Dify Enterprise Docker Compose 升级手册

本文适用于 Docker Compose 部署的 Dify Enterprise，包含通用升级路线，以及本目录当前部署从 **3.9.5 升级至 3.11.0** 的执行步骤。

> 适用范围：本文只覆盖 Dify Compose 栈。宿主机上的其他服务、外部反向代理、DNS、防火墙和监控需按实际环境另行评审。

## 0. 先读结论

本次升级必须安排维护窗口。3.11.0 引入 RBAC 强制迁移；在迁移完成前，普通成员可能无法访问工作区，知识库权限也可能不正确。

本目录的 Compose 使用相对路径 bind mount。因此，**不能把 3.11.0 解压到一个新目录后直接执行 `docker compose up -d`**：新目录会对应一套新的 `./volumes/`，从而启动一套空的 PostgreSQL、Redis、应用文件和 Weaviate 数据。

正确做法是：

1. 在临时目录准备、合并并校验 3.11.0 的配置。
2. 备份现有数据和配置。
3. 在当前生产目录中替换 Compose 程序文件，保留 `.env`、`volumes/` 和经过审核的本地定制。
4. 启动 3.11.0，执行 3.10.0 与 3.11.0 的迁移，再恢复业务流量。

## 1. 通用 Docker Compose 升级路线

### 1.1 发布前评审

每次跨版本升级都应逐个阅读中间版本的官方发布说明，记录：

- 是否有 breaking change、不可跳过版本或强制数据库迁移；
- Compose 文件、镜像、`env_file` 或环境变量体系是否变化；
- 是否删除了正在使用的向量库、追踪器、插件或存储集成；
- 目标版本是否存在未接受的 CVE 或许可风险；
- 回滚是否需要恢复数据库备份，而非只回退镜像。

同时确认目标镜像在维护窗口前可拉取，企业许可证仍有效，宿主机磁盘空间足够容纳数据库备份、对象存储备份和新镜像。

### 1.2 固化现状

在生产目录执行，输出仅保留在受控运维位置：

```bash
mkdir -p upgrade-evidence/$(date +%F)
docker compose ps > upgrade-evidence/$(date +%F)/before-ps.txt
docker compose images > upgrade-evidence/$(date +%F)/before-images.txt
docker compose config --quiet
cp -p .env upgrade-evidence/$(date +%F)/env.before
cp -p docker-compose.yaml upgrade-evidence/$(date +%F)/compose.before.yaml
```

不要把 `.env`、`docker compose config` 的完整输出或数据库备份上传到不受控的位置，其中通常含有密码和访问密钥。

### 1.3 备份、验证和回滚点

至少覆盖下列数据：

| 数据 | 推荐备份方式 | 恢复验证 |
| --- | --- | --- |
| PostgreSQL | `pg_dump` 逻辑备份，或停止写入后的卷快照 | 在隔离环境恢复并检查数据库可连接 |
| Redis | 确认 AOF/RDB 落盘并备份数据目录/卷 | 可启动并能读取键 |
| 对象存储或本地文件 | 对象存储桶全量备份；本地目录用文件级或卷快照 | 抽检附件和知识库原文件 |
| 向量库 | 按所用向量库做卷快照或官方导出 | 抽检知识库检索 |
| 配置 | `.env`、Compose、`envs/`、网关/反代、证书和覆盖文件 | 可由备份重新构建旧栈 |

在确认备份可读取前，不开始升级。执行过数据库迁移后，回滚应以“恢复备份 + 旧版镜像和配置”为主；不要假设旧镜像一定能读取已迁移的数据库。

### 1.4 新配置的生成和静态校验

以**目标版本包**携带的 `.env.example`、`dify-env-sync.py` 和 Compose 文件为准：

```bash
python3 dify-env-sync.py --dir /path/to/target-release
cd /path/to/target-release
docker compose config --quiet
docker compose pull
```

同步工具只处理环境变量，不复制 PostgreSQL、Redis、MinIO、向量库或应用文件。它提示“已删除”的变量时，应确认该变量没有非默认人工配置；必要时将配置迁移到目标版本支持的新变量或 `envs/` 文件中。

### 1.5 切换、迁移和验收

通用顺序如下：

```text
备份并验证
  → 生成目标配置并完成静态校验
  → 停止入口流量/启用维护页
  → 停止旧栈
  → 使用同一份持久化数据启动目标栈
  → 等待服务健康
  → 执行所有版本要求的迁移
  → 验收管理员和普通用户关键路径
  → 恢复入口流量
```

验收至少包括登录、模型调用、聊天/工作流、异步工作流、插件、知识库检索、文件上传下载、管理员功能、普通成员权限、审计与监控。发生阻断问题时，保持入口流量关闭，按已验证的恢复方案回滚。

## 2. 本次升级的已知事实和风险

### 2.1 当前部署形态

本目录当前使用 Dify Enterprise **3.9.5** 镜像。配置显示：

- 主数据库：PostgreSQL；
- 向量库：Weaviate；
- 文件存储：`opendal`；
- HTTPS：未由内置 Nginx 启用；
- 数据以相对 bind mount 保存，重点目录包括：
  - `./volumes/db/data`（PostgreSQL）；
  - `./volumes/redis/data`（Redis）；
  - `./volumes/app/storage`（应用本地文件）；
  - `./volumes/weaviate`（Weaviate）；
  - `./volumes/plugin_daemon`（插件守护进程数据）。

当前还有本地定制，替换官方包时不得遗漏：

- `docker-compose.override.yaml` 中企业后台前端 healthcheck；
- `gateway_configs/Caddyfile.template` 的 CORS/路由定制；
- 企业后台额外端口映射和访问地址相关配置；
- `.env` 内的外部 URL、存储、网关及企业版密钥。

### 2.2 3.10.0 必须纳入的事项

3.10.0 把 Compose 配置改为 `env_file` 分层架构。官方要求使用完整的新 Compose 包；手工维护时，`envs/enterprise/*` 必须存在或由 `.env` 正确覆盖，否则 Compose 不能启动。

3.10.0 还要求处理 Dify 数据库中的旧模型类型值。升级后在 API 容器执行：

```bash
docker compose exec api flask data-migrate legacy-model-types
```

该命令针对旧的 `text-generation`、`embeddings`、`reranking` 值。即使不确定是否存在，建议在维护窗口执行并保留输出。若有自定义 Redis Sentinel、Redis Cluster 或消息队列配置，还必须根据新变量体系复核。

### 2.3 3.11.0 必须纳入的事项

3.11.0 引入工作区 RBAC，并要求在恢复流量前依次执行：

```bash
docker compose exec api flask rbac-migrate-member-roles
docker compose exec api flask rbac-migrate-dataset-permissions --apply
docker compose exec api flask backfill-plugin-auto-upgrade
```

前两项分别修复成员角色映射和知识库权限映射；第三项初始化既有插件的自动升级状态。任何一项未完成时都不应恢复普通用户流量。

> 版本选择提示：企业版官网将 3.11.0 标为最新但不可跳过版本，并显示其有待处理的安全扫描项；官网同时推荐 3.9.7 作为 LTS。执行前应向 Dify 企业支持确认 3.11.0 是否适合当前生产环境及其补丁计划。

## 3. 3.9.5 → 3.11.0 详细执行步骤

以下命令假设当前目录就是生产目录；请在维护窗口前在测试或演练环境走通一次。`$CURRENT` 必须指向当前生产目录。

### 阶段 A：维护窗口前准备

```bash
export CURRENT=/path/to/dify-enterprise-0325
export STAGE=/opt/dify-upgrade-stage-3.11.0
export TS=$(date +%Y%m%d-%H%M%S)

mkdir -p "$STAGE"
curl -fL \
  https://langgenius.github.io/dify-enterprise-docker-compose/dify-docker-compose-3.11.0.tgz \
  -o "/tmp/dify-docker-compose-3.11.0.tgz"
tar -xzf /tmp/dify-docker-compose-3.11.0.tgz -C "$STAGE"

# 从生产配置创建候选配置；不要在此步骤启动容器。
cp -p "$CURRENT/.env" "$STAGE/.env"
python3 "$STAGE/dify-env-sync.py" --dir "$STAGE"

# 静态检查：仅验证 Compose 能解析，不会创建或启动容器。
(cd "$STAGE" && docker compose config --quiet)
```

审核候选 `.env`，确保以下值保留原值：外部 URL、`SECRET_KEY`、数据库/Redis 连接、`opendal` 存储配置、Weaviate 配置、企业版 URL 和密钥、邮件/SSO、网关与 CORS 配置。审阅同步脚本列出的已删除变量；有业务定制的变量不能未经映射就删除。

比较当前目录与候选包的定制相关文件，人工合并而非直接覆盖：

```bash
diff -u "$CURRENT/docker-compose.override.yaml" "$STAGE/docker-compose.override.yaml" || true
diff -u "$CURRENT/gateway_configs/Caddyfile.template" "$STAGE/gateway_configs/Caddyfile.template" || true
```

目标官方包若未包含 `docker-compose.override.yaml`，应在候选目录重新创建等价覆盖文件，并以 `docker compose config --quiet` 验证。

### 阶段 B：备份与停止流量

1. 通知用户维护窗口；在负载均衡器或反向代理启用维护页，停止新的写入请求。
2. 在 `$CURRENT` 目录记录容器和镜像清单。
3. 备份 PostgreSQL、Redis、`opendal` 对象存储/文件、Weaviate 和插件数据。
4. 验证备份文件不为空且可读取；将备份复制至独立存储。
5. 记录当前运行状态：

```bash
cd "$CURRENT"
mkdir -p "upgrade-evidence/$TS"
docker compose ps > "upgrade-evidence/$TS/before-ps.txt"
docker compose images > "upgrade-evidence/$TS/before-images.txt"
docker compose config --quiet
cp -p .env "upgrade-evidence/$TS/env.before"
```

> 不要执行 `docker compose down -v`，也不要执行任何 volume prune 命令。

### 阶段 C：将目标程序文件部署到生产目录

本步骤的目标是更新程序/Compose 文件，但继续使用 `$CURRENT/volumes/`。

```bash
cd "$CURRENT"

# 先停止旧容器；不加 -v。
docker compose down

# 将旧的非数据文件留档；volumes/、.env 和本地定制不在此处删除。
mkdir -p "upgrade-evidence/$TS/replaced-files"
cp -a docker-compose.yaml .env.example dify-env-sync.py dify-env-sync.sh \
  gateway_configs "upgrade-evidence/$TS/replaced-files/"
```

随后将 `$STAGE` 中的目标版本文件复制到 `$CURRENT`。可按站点变更管理工具执行；手工执行时需保留：

- `$CURRENT/volumes/`；
- 已审核的 `$CURRENT/.env`（以 `$STAGE/.env` 的合并结果替换）；
- 已合并的 `docker-compose.override.yaml`；
- 已合并的 `gateway_configs/Caddyfile.template`；
- 本地证书、额外反向代理和运行时生成文件。

在已经把本地定制合并进 `$STAGE` 后，可使用下面的复制方式。这里**刻意不使用 `--delete`**，以免在未盘点前删除站点特有文件；同时明确排除持久化数据和已留档的升级证据。

```bash
rsync -a \
  --exclude '.env' \
  --exclude 'volumes/' \
  --exclude 'upgrade-evidence/' \
  "$STAGE/" "$CURRENT/"
cp -p "$STAGE/.env" "$CURRENT/.env"
```

若站点通过 Git、Ansible 或其他发布工具管理 Compose 文件，应使用等价的排除规则，而不是混用多种复制方式。

复制完成后，必须确认 `envs/enterprise/` 等目标包目录存在，并在生产目录验证：

```bash
cd "$CURRENT"
test -d envs/enterprise
docker compose config --quiet
docker compose pull
```

### 阶段 D：启动和迁移

```bash
cd "$CURRENT"
docker compose up -d
docker compose ps
```

等待 API、worker、数据库、Redis、网关、企业服务、插件守护进程和 Weaviate 进入健康状态。确认 API 容器可执行 Flask 命令后，按以下顺序执行迁移：

```bash
# 3.10.0：模型类型迁移
docker compose exec api flask data-migrate legacy-model-types

# 3.11.0：RBAC 和插件状态迁移
docker compose exec api flask rbac-migrate-member-roles
docker compose exec api flask rbac-migrate-dataset-permissions --apply
docker compose exec api flask backfill-plugin-auto-upgrade
```

保存四条命令的完整输出到维护记录。任何命令失败时，不恢复入口流量；先收集 `docker compose logs`、数据库迁移日志和命令输出，再根据原因决定修复或回滚。

### 阶段 E：验收与恢复流量

在恢复外部流量前，使用管理员账号和至少一个普通成员账号分别验证：

- 管理员、企业后台和普通工作区可登录；
- 普通成员拥有预期工作区角色；
- 知识库可见范围、成员授权和检索结果正确；
- 文件上传、下载及历史文件访问正常；
- 聊天应用、Chatflow、Workflow 和异步任务能完成；
- worker 正在消费工作流队列，尤其是 `workflow_based_app_execution`；
- 模型凭证、插件调用、外部工具和审计记录正常；
- 网关 CORS、企业后台额外端口和原有访问域名/IP 均可访问。

通过验收后，解除维护页并持续观察 API、worker、Redis、PostgreSQL 和网关日志至少一个业务高峰周期。

### 阶段 F：失败处理和回滚

若在数据库迁移前发现 Compose、镜像或网关问题：停止新容器，恢复旧 Compose 文件和旧镜像，继续使用原数据目录。

若已执行数据库迁移且需要回滚：

1. 保持入口流量关闭；
2. 停止新栈，但不要删除卷；
3. 恢复升级前验证过的 PostgreSQL、Redis、对象存储/文件和向量库备份；
4. 恢复 3.9.5 的 Compose、`.env`、网关与覆盖文件；
5. 启动旧栈并执行与上线相同的关键路径验收；
6. 留存故障日志，不在未分析迁移失败原因时重复升级。

## 4. 官方参考

- [Dify Enterprise 版本总览](https://ee.dify.ai/)
- [Dify Enterprise 3.10.0 发布与迁移说明](https://ee.dify.ai/releases/v3.10.0/)
- [Dify Enterprise 3.11.0 发布与迁移说明](https://ee.dify.ai/releases/v3.11.0/)
- [3.11.0 官方 Docker Compose 包](https://langgenius.github.io/dify-enterprise-docker-compose/dify-docker-compose-3.11.0.tgz)
