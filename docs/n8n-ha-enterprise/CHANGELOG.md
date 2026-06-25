# 变更日志

## [未发布]

### 变更
- 2026-06-25: Traefik 对外端口从 5680/5681 改为标准 80/443（适配严格端口策略，仅开放 80/443 的服务器）
- 2026-06-25: Traefik Dashboard 端口 8889 改为绑 127.0.0.1，外部访问通过 SSH 隧道
- 2026-06-25: n8n 主机名从 `n8n.local` 改为正式域名 `li19dksfai11vm.bmwgroup.net`
- 2026-06-25: n8n 协议从 `http` 改为 `https`，WEBHOOK_URL / EDITOR_BASE_URL 同步更新
- 2026-06-25: 开启 `N8N_SECURE_COOKIE=true`（HTTPS 下必须）
- 2026-06-25: Grafana 端口 3001 改为绑 127.0.0.1，外部访问通过 Traefik `/grafana` 子路径
- 2026-06-25: Grafana 增加 `GF_SERVER_ROOT_URL` / `GF_SERVER_SERVE_FROM_SUB_PATH` 子路径配置
- 2026-06-25: Traefik dynamic.yml 增加 Grafana 子路径路由（PathPrefix + StripPrefix + priority）
- 2026-06-25: Traefik 增加 TLS 配置块和 certs 目录挂载（需手动放置 cert.pem / key.pem）

### 新增
- 2026-06-25: CHANGELOG.md 文件

### 部署后必须做的事
1. 在 `./config/traefik/certs/` 下放置企业 CA 签发的 `cert.pem` 和 `key.pem`（HTTPS 必需）
2. 确保服务器防火墙已开放 80 和 443 端口
3. 确保 DNS 已将 `li19dksfai11vm.bmwgroup.net` 解析到本机
4. 重启 Traefik 与 Grafana 容器：
   ```bash
   docker compose up -d --force-recreate traefik grafana
   ```
5. 验证访问：
   - n8n: `https://li19dksfai11vm.bmwgroup.net/`
   - Grafana: `https://li19dksfai11vm.bmwgroup.net/grafana/`
   - Traefik Dashboard（仅本机）: `http://localhost:8889/` 或 SSH 隧道访问
