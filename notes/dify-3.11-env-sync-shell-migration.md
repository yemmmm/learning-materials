# Dify Enterprise 3.11 环境变量同步（Shell 版）

适用场景：服务器无法运行 Python，但需要从旧版 Dify Enterprise 的顶层 `.env` 升级到 3.11 的分层 `envs/` 配置结构。

## 脚本位置

```text
/home/yangxiang/deployed-services/dify-enterprise-3.11.0/dify-env-sync.sh
```

该脚本不依赖 Python，仅需要 Bash、awk、find、cp、mv 等常见系统命令。

## 推荐执行方式

先把旧部署的 `.env` 复制到新的 3.11 发布目录，再在新目录执行同步。不要直接覆盖仍在运行的旧版本目录。

```bash
CURRENT=/home/yangxiang/deployed-services/dify-enterprise-0325
TARGET=/home/yangxiang/deployed-services/dify-enterprise-3.11.0

cp -p "$CURRENT/.env" "$TARGET/.env"
bash "$TARGET/dify-env-sync.sh" --dir "$TARGET"

cd "$TARGET"
docker compose config --quiet
```

## 迁移规则

1. 顶层 `.env.example` 仍包含的变量：保留旧 `.env` 的自定义值。
2. 新顶层模板新增的变量：写入 3.11 默认值。
3. 旧 `.env` 已移出顶层模板、但只属于一个 `envs/**/*.env(.example)` 文件的变量：自动迁入对应结构化文件；可选组件模板会自动由 `*.env.example` 生成 `*.env`。
4. 同时匹配多个 `envs` 文件的变量：不猜测归属，保留在新 `.env` 末尾的 `Legacy overrides` 区域，保证升级不会静默丢失配置。
5. 在 3.11 模板中完全找不到的变量：不迁入；应根据升级说明确认其是否已经废弃或改名。

默认会创建备份：

```text
env-backup/.env.backup_YYYYMMDD_HHMMSS
```

## 参数

```bash
# 不创建 .env 备份（一般不建议）
bash dify-env-sync.sh --dir /path/to/3.11.0 --no-backup

# 仅执行传统顶层 .env 同步，不自动迁移到 envs/
bash dify-env-sync.sh --dir /path/to/3.11.0 --no-envs-migration
```

## 验证

同步后先检查 Compose 能否解析，再决定是否拉取镜像或启动服务：

```bash
docker compose config --quiet
```

重点复核 `.env` 末尾的 `Legacy overrides`，并按实际启用的组件将其中值逐步迁移到对应的 `envs/*.env` 文件。
