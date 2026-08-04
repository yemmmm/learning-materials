#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-04 09:54 本机时间
# Context: 定位 POST /console/api/apps/imports 400 的直接原因：API 进程实际使用的 Marketplace URL/代理主机是否可解析，并确认容器内对 /api/v1/plugins/batch 的 DNS/HTTP 连通性。
# Cmds: 3 条

# 1. 查看运行中 API 容器实际加载的 Marketplace、代理和插件守护进程配置，排除只改 .env 但未重建容器。
cid="$(docker-compose ps -q api 2>/dev/null | head -1)"
if [ -n "$cid" ]; then
  docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$cid" 2>&1 \
    | grep -E '^(MARKETPLACE_ENABLED|MARKETPLACE_API_URL|PLUGIN_DAEMON_URL|HTTP_PROXY|HTTPS_PROXY|ALL_PROXY|NO_PROXY)=' \
    | head -20
else
  echo 'api: container not found'
fi

# 2. 从同一个 API 容器解析 Marketplace 主机并请求插件批量清单；失败阶段可区分 DNS、代理、TLS 与 HTTP 状态。
docker-compose exec -T api python - <<'PY' 2>&1 | head -25
import os, socket
from urllib.parse import urlparse
import httpx
from core.helper import marketplace

base = str(marketplace.marketplace_api_url)
parsed = urlparse(base)
host = parsed.hostname
port = parsed.port or (443 if parsed.scheme == "https" else 80)
print("loaded_url=", base)
print("host=", host, "port=", port)
for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
    value = os.getenv(key)
    print(key, urlparse(value).hostname if value else "<unset>")
try:
    socket.getaddrinfo(host, port)
    print("dns=ok")
except Exception as exc:
    print("dns_error=", repr(exc))
try:
    response = httpx.post(base.rstrip("/") + "/api/v1/plugins/batch", json={"plugin_ids": ["langgenius/openai"]}, timeout=20)
    print("http=", response.status_code, response.text[:200].replace("\n", " "))
except Exception as exc:
    print("http_error=", type(exc).__name__, repr(exc))
PY

# 3. 提取最近导入请求的后端堆栈，确认 400 是否仍由 marketplace.batch_fetch_plugin_manifests 触发。
docker-compose logs --since 30m --timestamps api 2>&1 \
  | grep -iE 'Failed to import app|generate_latest_dependencies|batch_fetch_plugin_manifests|Name or service|ConnectError|marketplace' \
  | tail -25
