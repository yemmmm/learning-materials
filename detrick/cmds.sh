#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-05 21:00
# Context: 升级后 OIDC SSO 失败；确认运行版本、invalid_scope 产生在哪一层，以及 OIDC 配置存储位置
# Cmds: 3 条
# 操作提示：先重新发起一次 SSO 登录，看到报错后立即执行以下命令

# 1. 确认升级后实际运行的 SSO 相关容器镜像和状态
docker-compose ps 2>&1 | grep -E '(^Name|dify-enterprise|dify-gateway|api)' | head -20 && docker-compose images 2>&1 | grep -E '(^Container|dify-enterprise|dify-gateway|api)' | head -20

# 2. 查看刚才这次登录在网关、企业服务和 API 三层的 OIDC/Scope/State 证据
docker-compose logs --since 10m dify-gateway dify-enterprise api 2>&1 | grep -iE 'oidc|sso|invalid_scope|unknown|scope|state|callback|error' | tail -30

# 3. 仅列出数据库中与 SSO/OIDC 有关的表名和字段名，不读取配置值或密钥
docker-compose exec -T db_postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT table_schema||chr(46)||table_name||chr(46)||column_name FROM information_schema.columns ORDER BY table_schema,table_name,ordinal_position;"' 2>&1 | grep -iE 'sso|oidc|oauth|scope' | head -30
