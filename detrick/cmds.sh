#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-05 22:21
# Context: Provider 与管理 API 均正常；对比 Dify 实际请求的 scope 和 IdP discovery 声明的 scopes_supported
# Cmds: 2 条

# 1. 调用 OIDC 登录入口，只显示授权请求的 scope、state 是否存在及参数名，不输出完整 URL/client_id/state
docker-compose exec -T api python - <<'PY' 2>&1 | head -30
import json
from urllib.parse import parse_qs, urlsplit
import requests

r = requests.get("http://dify-enterprise:8082/console/api/enterprise/sso/oidc/login", timeout=15, allow_redirects=False)
print("status=%s content_type=%s" % (r.status_code, r.headers.get("content-type", "")))
urls = []
if r.headers.get("location"):
    urls.append(r.headers["location"])
try:
    body = r.json()
    print("body_keys=%s" % sorted(body.keys()) if isinstance(body, dict) else "body_type=%s" % type(body).__name__)
    def walk(value, key=""):
        if isinstance(value, dict):
            for name, child in value.items():
                walk(child, name)
        elif isinstance(value, list):
            for child in value:
                walk(child, key)
        elif isinstance(value, str) and value.startswith(("http://", "https://")) and ("url" in key.lower() or "redirect" in key.lower()):
            urls.append(value)
    walk(body)
except Exception:
    pass
if not urls:
    print("authorization_url=NOT_FOUND")
for url in urls[:2]:
    parsed = urlsplit(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    print("authorization_target=%s%s" % (parsed.netloc, parsed.path))
    print("query_keys=%s" % sorted(query.keys()))
    print("scope=%r" % query.get("scope", [None])[0])
    print("state_present=%s state_empty=%s" % ("state" in query, query.get("state", [""])[0] == ""))
PY

# 2. 读取数据库中的 OIDC issuer，并只显示 discovery 状态及 IdP 声明支持的 scopes
docker-compose exec -T api python - <<'PY' 2>&1 | head -30
import json
import os
import psycopg2
import requests

def pick(*names):
    return next((os.environ.get(name) for name in names if os.environ.get(name)), None)

conn = psycopg2.connect(
    host=pick("DB_HOST"), port=pick("DB_PORT") or "5432",
    dbname=pick("ENTERPRISE_DB_NAME"),
    user=pick("ENTERPRISE_DB_USER", "DB_USER", "DB_USERNAME"),
    password=pick("ENTERPRISE_DB_PASS", "DB_PASS", "DB_PASSWORD"),
    sslmode=pick("DB_SSL_MODE") or "disable",
)
cur = conn.cursor()
cur.execute("SELECT value FROM sys_settings WHERE key=%s", ("USER_SSO_SETTINGS",))
data = json.loads(cur.fetchone()[0])
issuer = data["sso_idp_provider"]["oidc_config"]["issuer_url"]
metadata_url = issuer if ".well-known/openid-configuration" in issuer else issuer.rstrip("/") + "/.well-known/openid-configuration"
r = requests.get(metadata_url, timeout=15)
print("discovery_status=%s content_type=%s" % (r.status_code, r.headers.get("content-type", "")))
metadata = r.json()
print("issuer_matches=%s" % (metadata.get("issuer", "").rstrip("/") == issuer.replace("/.well-known/openid-configuration", "").rstrip("/")))
print("authorization_endpoint_present=%s" % bool(metadata.get("authorization_endpoint")))
print("token_endpoint_present=%s" % bool(metadata.get("token_endpoint")))
print("scopes_supported=%r" % metadata.get("scopes_supported"))
cur.close()
conn.close()
PY
