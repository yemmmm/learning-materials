# Dify 企业版 3.7.5 → 3.8.0 升级记录

## 升级日期
2026-06-05

## 镜像 Tag 变更

| 服务 | 旧 Tag (3.7.5) | 新 Tag (3.8.0) |
|------|---------------|---------------|
| dify-api | `3d2aea11a30200d6bf4be3033b6b1ff63bb87ffc` | `7a1f0e32580a963404801ca4e7f53afa88db6aea` |
| dify-web | `3d2aea11a30200d6bf4be3033b6b1ff63bb87ffc` | `7a1f0e32580a963404801ca4e7f53afa88db6aea` |
| dify-enterprise | `0.14.4` | `0.15.0` |
| dify-enterprise-frontend | `0.14.4` | `0.15.0` |
| dify-plugin-manager | `0.14.4` | `0.15.0` |
| dify-audit | `0.14.4` | `0.15.0` |
| enterprise_gateway | `0.14.4` | `0.15.0` |
| dify-plugin-daemon | `0.5.0-local` | `0.5.3-local` |
| dify-sandbox | `0.2.12` | `0.2.12` (不变) |
| RELEASE_VERSION | `3.7.5 (Docker)` | `3.8.0 (Docker)` |

## 新增服务 (3.8.0)
- `dify-enterprise-collector:0.15.0` — OpenTelemetry 数据收集器 (未在当前部署中添加)

## 升级方法

在 `dify-enterprise-0325/docker-compose.yaml` 中执行以下替换：

```bash
sed -i 's/3d2aea11a30200d6bf4be3033b6b1ff63bb87ffc/7a1f0e32580a963404801ca4e7f53afa88db6aea/g' docker-compose.yaml
sed -i 's/0.14.4/0.15.0/g' docker-compose.yaml  # 仅 langgenius 镜像
sed -i 's/0.5.0-local/0.5.3-local/g' docker-compose.yaml
sed -i 's/3.7.5 (Docker)/3.8.0 (Docker)/g' docker-compose.yaml
```

## 注意事项

1. 升级前务必备份数据库: `tar -czf backup.tgz volumes .env`
2. 升级后拉取新镜像: `docker compose pull`
3. 重启服务: `docker compose up -d`
4. 如需添加 enterprise-collector 服务，参考 3.8.0 官方 docker-compose 模板
