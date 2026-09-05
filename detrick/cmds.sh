#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-05 21:23
# Context: 已确认使用外部 PostgreSQL；验证 api/enterprise 数据库配置是否一致，并读取外部 enterprise 库中的 SSO 协议与 scopes
# Cmds: 2 条

# 1. 比较 api 与 dify-enterprise 的数据库目标；敏感变量按变量名完整遮蔽
for svc in api dify-enterprise; do echo "service=$svc"; docker-compose exec -T "$svc" sh -c env 2>&1 | grep -E '^(DB_(ENGINE|HOST|PORT|USER|USERNAME|PASS|PASSWORD|SSL_MODE)|DIFY_DB_|ENTERPRISE_DB_)' | awk -F= 'BEGIN{IGNORECASE=1} $1 ~ /(PASS|PASSWORD|SECRET|TOKEN|KEY|USER)/ {print $1 "=[REDACTED]"; next} {print}'; done | head -30

# 2. 从 api 容器连接外部 enterprise 数据库，只输出 SSO 配置结构、协议、启用状态和 scopes
docker-compose exec -T api python - <<'PY' 2>&1 | head -30
import json
import os
import psycopg2

def pick(*names):
    return next((os.environ.get(name) for name in names if os.environ.get(name)), None)

conn = psycopg2.connect(
    host=pick("DB_HOST"),
    port=pick("DB_PORT") or "5432",
    dbname=pick("ENTERPRISE_DB_NAME"),
    user=pick("ENTERPRISE_DB_USER", "DB_USER", "DB_USERNAME"),
    password=pick("ENTERPRISE_DB_PASS", "DB_PASS", "DB_PASSWORD"),
    sslmode=pick("DB_SSL_MODE") or "disable",
)
cur = conn.cursor()
cur.execute("SELECT current_database(), to_regclass('public.sys_settings')")
print("database=%s sys_settings=%s" % cur.fetchone())
keys = ("USER_SSO_SETTINGS", "WEB_SSO_SETTINGS", "DASHBOARD_SSO_SETTINGS")
cur.execute("SELECT key, value FROM sys_settings WHERE key = ANY(%s) ORDER BY key", (list(keys),))
rows = cur.fetchall()
print("sso_rows=%d" % len(rows))
for key, raw in rows:
    try:
        data = json.loads(raw)
    except Exception:
        print("%s length=%d json=UNPARSEABLE" % (key, len(raw)))
        continue
    print("%s length=%d top_keys=%s" % (key, len(raw), sorted(data.keys())))
    def walk(value, path=""):
        if isinstance(value, dict):
            for name, child in value.items():
                child_path = "%s.%s" % (path, name) if path else name
                if name.lower() in {"scope", "scopes", "protocol", "type", "enabled"}:
                    print("  %s=%s" % (child_path, json.dumps(child, ensure_ascii=True)))
                if isinstance(child, (dict, list)):
                    walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                if isinstance(child, (dict, list)):
                    walk(child, "%s[%d]" % (path, index))
    walk(data)
cur.close()
conn.close()
PY
