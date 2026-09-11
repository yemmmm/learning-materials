#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-11
# Context: SSO 已有用户邀请后 pending；移除后 workspace 丢失。核对同邮箱是否对应多个 account_id。
# Cmds: 3 条；在原 Compose 目录、原 shell 逐块粘贴，不用 bash 执行（docker-compose 可能是函数）。
# 全部只读；不重现删除、不改账户、不初始化 Flask 应用。原 n8n 暂停探针保留于 Git 历史。

# 1. 输入受影响用户并核对镜像；登录 ID 可从该用户 GET /console/api/account/profile 响应的 id 取得。
read -r -p 'API Compose service [api]: ' DTR_API
DTR_API=${DTR_API:-api}
read -r -p 'Affected email (original case): ' DTR_EMAIL
read -r -p 'Affected user current profile id (optional, Enter to skip): ' DTR_LOGIN_ID
DTR_CIDS=$(docker-compose ps -q)
if [ -n "$DTR_CIDS" ]; then
  docker inspect --format '{{index .Config.Labels "com.docker.compose.service"}} {{.Config.Image}}' $DTR_CIDS 2>&1 | sed -E 's@[^ ]*/(dify-ee-[^ /]+)@\1@g' | head -20
else
  echo 'NO_CONTAINERS: check Compose directory'
fi

# 2. 查询同邮箱账户与 workspace 关系；不输出邮箱原文、SSO token 或连接串，最多 26 行结果。
docker-compose exec -T -e DTR_EMAIL="$DTR_EMAIL" -e DTR_LOGIN_ID="$DTR_LOGIN_ID" "$DTR_API" python - <<'PY' 2>&1 | head -30
import os, json, logging
from uuid import UUID
logging.disable(logging.CRITICAL)
def emit(kind, **data):
    print(json.dumps(dict(check=kind, **data), ensure_ascii=True, default=str))
try:
    from configs import dify_config
    from sqlalchemy import create_engine, text
    email = os.environ['DTR_EMAIL'].strip()
    if not email or '@' not in email: raise ValueError('email required')
    login = os.environ.get('DTR_LOGIN_ID', '').strip()
    login = str(UUID(login)) if login else None
    engine = create_engine(dify_config.SQLALCHEMY_DATABASE_URI, connect_args={'connect_timeout': 8})
    params = dict(email=email, login=login)
    with engine.connect() as conn:
        conn.execute(text('SET TRANSACTION READ ONLY'))
        conn.execute(text("SET LOCAL statement_timeout = '8s'"))
        accounts = conn.execute(text('''SELECT a.id, a.status, a.created_at, a.initialized_at, a.last_login_at,
            a.email <> lower(a.email) AS stored_has_upper, a.email = :email AS exact_input_match,
            a.id = CAST(:login AS uuid) AS is_current_login,
            (SELECT count(*) FROM tenant_account_joins j WHERE j.account_id=a.id) AS workspace_count
            FROM accounts a WHERE lower(a.email)=lower(:email) OR a.id=CAST(:login AS uuid)
            ORDER BY a.created_at, a.id LIMIT 7'''), params).mappings().all()
        emit('account_summary', returned=min(len(accounts),6), truncated=len(accounts)>6,
             login_id_supplied=bool(login), rbac_enabled=bool(dify_config.RBAC_ENABLED))
        for row in accounts[:6]: emit('account', **dict(row))
        joins = conn.execute(text('''SELECT j.account_id, j.tenant_id, j.role AS legacy_join_role,
            j.current, j.created_at AS joined_at, t.status AS workspace_status, a.id IS NULL AS account_missing
            FROM tenant_account_joins j LEFT JOIN accounts a ON a.id=j.account_id
            LEFT JOIN tenants t ON t.id=j.tenant_id
            WHERE lower(a.email)=lower(:email) OR j.account_id=CAST(:login AS uuid)
            ORDER BY j.account_id, j.created_at, j.tenant_id LIMIT 19'''), params).mappings().all()
        emit('membership_summary', returned=min(len(joins),18), truncated=len(joins)>18)
        for row in joins[:18]: emit('membership', **dict(row))
except Exception as e:
    emit('ERROR', error_type=type(e).__name__, sqlstate=getattr(getattr(e,'orig',None),'pgcode',None))
PY

# 3. 抽取现场邮箱匹配和 pending 删除分支；只读取源码，不调用函数，最多 28 行。
docker-compose exec -T "$DTR_API" python - <<'PY' 2>&1 | head -30
import ast
from pathlib import Path
path=Path('/app/api/services/account_service.py')
if not path.exists():
    print('SOURCE_NOT_FOUND'); raise SystemExit
source=path.read_text(); lines=source.splitlines(); tree=ast.parse(source)
checks=[('get_account_by_email_with_case_fallback', ('filter_by(', 'Account.email', 'email.lower', 'return account', 'return query', 'return session')),
        ('remove_member_from_tenant', ('delete(', 'filter_by(', 'AccountStatus.PENDING', 'remaining_joins', 'TenantAccountJoin.account_id', 'sync_workspace', 'delete_rbac'))]
for name, needles in checks:
    nodes=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    if not nodes:
        print(name+': NOT_FOUND'); continue
    node=nodes[0]; print(name+':')
    hits=[(i+1,lines[i].strip()) for i in range(node.lineno-1,node.end_lineno) if any(x in lines[i] for x in needles)]
    for number,line in hits[:12]: print(str(number)+': '+line)
    if len(hits)>12: print('TRUNCATED')
PY
