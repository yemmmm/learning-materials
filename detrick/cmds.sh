#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-04 10:31 本机时间
# Context: 区分 marketplace.dify.ai 的解析失败发生在宿主机 DNS/封闭网络，还是仅发生在 API 容器的 Docker DNS，并确认宿主机与容器的 HTTPS 访问差异。
# Cmds: 2 条

# 1. 在宿主机检查 DNS 配置、marketplace.dify.ai 解析和 HTTPS 出口，作为容器网络的对照基线。
{
  echo '--- host resolv.conf ---'
  sed -n '1,12p' /etc/resolv.conf
  echo '--- host dns ---'
  getent ahosts marketplace.dify.ai 2>&1 | head -8
  echo '--- host https ---'
  curl -I -L --connect-timeout 5 --max-time 10 https://marketplace.dify.ai 2>&1 | head -15
} 2>&1 | head -35

# 2. 在实际 API 容器内检查 resolver，并调用 Dify 使用的插件批量接口；直接失败即证明容器侧 DNS/出口未打通。
docker-compose exec -T api python - <<'PY' 2>&1 | head -30
import socket
from pathlib import Path
from urllib.parse import urlparse
import httpx
from core.helper import marketplace

base = str(marketplace.marketplace_api_url).rstrip('/')
host = urlparse(base).hostname
print('loaded_url=', base)
print('--- api resolv.conf ---')
print(Path('/etc/resolv.conf').read_text().strip())
try:
    print('api_dns=', socket.getaddrinfo(host, 443))
except Exception as exc:
    print('api_dns_error=', repr(exc))
try:
    response = httpx.post(
        base + '/api/v1/plugins/batch',
        json={'plugin_ids': ['langgenius/openai']},
        timeout=20,
    )
    print('api_http=', response.status_code, response.text[:200].replace('\n', ' '))
except Exception as exc:
    print('api_http_error=', type(exc).__name__, repr(exc))
PY
