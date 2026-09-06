#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 20:30
# Context: 不确定本机 db 服务里存的是什么库、rbac 连的 PG 是不是它。本轮先摸清：①db 服务身份与库清单 ②rbac 实际连的 DB 主机
# Cmds: 3 条

# 1. db 容器的身份信息（用户名/密码/默认库）
docker-compose exec -T db env | grep -iE 'postgres_|pgdata' | head -10

# 2. db 容器里现有的数据库清单（看有没有 dify_enterprise 库）
PGPASSWORD=difyai123456 docker-compose exec -T db psql -U postgres -c "select datname from pg_database" 2>&1 | head -20

# 3. rbac 容器连的 DB 主机地址（确认连的是 db 服务还是别的 PG）
docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' $(docker-compose ps -q dify-enterprise-rbac) | grep -iE 'host|addr' | head -5
