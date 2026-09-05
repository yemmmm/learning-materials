#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-05 21:09
# Context: 上轮三条均为空；验证执行目录/服务名、企业数据库连接，以及 USER_SSO_SETTINGS 的 OIDC scopes 是否丢失
# Cmds: 3 条

# 1. 不做过滤，确认当前目录对应的 Compose 项目及真实服务名
pwd; docker-compose config --services 2>&1 | head -30

# 2. 查看 dify-enterprise 实际镜像及关键运行时变量；密码、用户和密钥值会隐藏
cid=$(docker-compose ps -q dify-enterprise 2>/dev/null); if [ -z "$cid" ]; then echo 'ERROR: 当前 Compose 项目没有运行 dify-enterprise 服务'; else docker inspect "$cid" --format 'image={{.Config.Image}}'; docker inspect "$cid" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>&1 | grep -E '^(DB_(ENGINE|HOST|PORT|USER|PASS)|DIFY_DB_|ENTERPRISE_DB_|DIFY_CONSOLE_|ENTERPRISE_URL|ENTERPRISE_SECRET_KEY_SALT|CONSOLE_SSO_)' | sed -E '/(PASS|SECRET|KEY|USER)=/ s/=.*/=[SET]/' | head -29; fi

# 3. 查询 enterprise 数据库的 SSO 设置：只显示记录名、长度、协议和 scopes，不读取 client secret
docker-compose exec -T db_postgres sh -lc 'psql -U "$POSTGRES_USER" -d enterprise -Atc "SELECT key, length(value), COALESCE(value::jsonb#>>\$\${protocol}\$\$,value::jsonb#>>\$\${type}\$\$,\$\$[NO_PROTOCOL]\$\$), COALESCE(value::jsonb#>>\$\${oidc_config,scopes}\$\$,value::jsonb#>>\$\${oidcConfig,scopes}\$\$,value::jsonb#>>\$\${scopes}\$\$,\$\$[NO_SCOPES]\$\$) FROM sys_settings WHERE key IN (\$\$USER_SSO_SETTINGS\$\$,\$\$WEB_SSO_SETTINGS\$\$,\$\$DASHBOARD_SSO_SETTINGS\$\$) ORDER BY key;"' 2>&1 | head -30
