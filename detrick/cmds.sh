#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-05 21:59
# Context: 数据库有 OIDC provider 但管理页不显示；检查 OIDC 专用字段完整性及后端读取错误
# Cmds: 2 条
# 操作提示：先刷新一次管理员认证配置页面，再立即执行以下命令

# 1. 查看刷新页面时 dify-enterprise 后端的最近输出，不预先过滤错误关键词
docker-compose logs --since 5m --timestamps dify-enterprise 2>&1 | tail -30

# 2. 安全检查 USER_SSO_SETTINGS 的时间戳及 OIDC 专用字段状态，不输出字段值或密钥
docker-compose exec -T api python - <<'PY' 2>&1 | head -30
import json
import os
import psycopg2

def pick(*names):
    return next((os.environ.get(name) for name in names if os.environ.get(name)), None)

def state(value):
    if value is None:
        return "MISSING"
    if isinstance(value, str):
        return "EMPTY" if not value.strip() else "SET(length=%d)" % len(value)
    return str(value) if isinstance(value, bool) else "SET(type=%s)" % type(value).__name__

conn = psycopg2.connect(
    host=pick("DB_HOST"), port=pick("DB_PORT") or "5432",
    dbname=pick("ENTERPRISE_DB_NAME"),
    user=pick("ENTERPRISE_DB_USER", "DB_USER", "DB_USERNAME"),
    password=pick("ENTERPRISE_DB_PASS", "DB_PASS", "DB_PASSWORD"),
    sslmode=pick("DB_SSL_MODE") or "disable",
)
cur = conn.cursor()
cur.execute("SELECT created_at, updated_at, value FROM sys_settings WHERE key=%s", ("USER_SSO_SETTINGS",))
row = cur.fetchone()
if not row:
    print("USER_SSO_SETTINGS=MISSING")
else:
    created_at, updated_at, raw = row
    data = json.loads(raw)
    provider = data.get("sso_idp_provider") or {}
    oidc = provider.get("oidc_config") or {}
    oauth2 = provider.get("oauth2_config") or {}
    print("created_at=%s updated_at=%s" % (created_at, updated_at))
    print("protocol=%s provider_type=%s" % (provider.get("protocol"), provider.get("provider")))
    for name in ("issuer_url", "client_id", "client_secret", "enable_pkce"):
        print("oidc_config.%s=%s" % (name, state(oidc.get(name))))
    print("oauth2_config.scopes=%s (not used when protocol=oidc)" % state(oauth2.get("scopes")))
cur.close()
conn.close()
PY
