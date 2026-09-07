#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 23:07
# Context: Agent 白名单拒绝及邀请后资源授权待查；兼容宿主旧 Python 和 ~/.bashrc 中的 docker-compose() 函数；全部只读。
# Cmds: 3 条
# 在服务器 Compose 目录执行。先让受影响成员各复现一次 Agent 打开失败、旧工作流打开失败。
# 整份执行请用 source ./cmds.sh（在已有 docker-compose 函数的 Bash 中），不要用 bash cmds.sh。

# 1. 镜像、有效 RBAC 开关及 worker 实际订阅队列（不输出连接串或密钥；最多 20 行）
if declare -F docker-compose >/dev/null; then export -f docker-compose; fi
python3 - <<'PY'
import json, subprocess
def run(args):
    if args[0] == 'docker-compose':
        args = ['bash', '-c', 'docker-compose "$@"', 'rbac-probe'] + args[1:]
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=25)
for svc in ['api', 'worker', 'dify-enterprise-rbac']:
    ids = run(['docker-compose', 'ps', '-q', svc]).stdout.split()
    if not ids:
        print(svc, 'NO_CONTAINER'); continue
    for cid in ids[:3]:
        obj = json.loads(run(['docker', 'inspect', cid]).stdout)[0]
        env = dict(x.split('=', 1) for x in obj['Config'].get('Env', []) if '=' in x)
        print(svc, obj['Name'], obj['Config']['Image'], 'state='+obj['State']['Status'],
              'RBAC_ENABLED='+env.get('RBAC_ENABLED', '<unset>'),
              'env_has_app_rbac='+str('app_rbac' in env.get('CELERY_QUEUES', '').split(',')))
r = run(['docker-compose', 'exec', '-T', 'worker', 'celery', '-A', 'app.celery', 'inspect', 'active_queues', '--timeout=5', '--json'])
try:
    data = json.loads(r.stdout)
    for name, queues in list(data.items())[:8]:
        names = [q.get('name') for q in queues] if isinstance(queues, list) else []
        print('ACTIVE_QUEUES', name, 'app_rbac='+str('app_rbac' in names), 'count='+str(len(names)))
    if not data: print('ACTIVE_QUEUES no replies; not proof of missing subscription')
except (ValueError, AttributeError):
    print('ACTIVE_QUEUES unavailable; exit='+str(r.returncode)+'; not proof of missing subscription')
PY

# 2. 自动提取最近 15 分钟最多 2 个拒绝案例，GET 查询白名单/成员策略/角色（最多 20 行；不打印密钥或姓名邮箱）
# 请受影响成员先分别打开一次 Agent 和加入工作区前已有的工作流，然后执行。
if declare -F docker-compose >/dev/null; then export -f docker-compose; fi
python3 - <<'PY'
import json, subprocess, uuid
compose = ['bash', '-c', 'docker-compose "$@"', 'rbac-probe']
r = subprocess.run(compose + ['logs', '--since', '15m', '--tail=1200', '--no-color', 'dify-enterprise-rbac'],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=25)
cases = []
for line in reversed(r.stdout.splitlines()):
    try:
        obj = json.loads(line[line.index('{'):])
        a = obj.get('attributes', obj)
        if a.get('resource_type') != 'app' or 'denied' not in str(obj.get('message', '')):
            continue
        item = {k: str(uuid.UUID(a[k])) for k in ['tenant_id', 'account_id', 'resource_id']}
        if item not in cases: cases.append(item)
        if len(cases) == 2: break
    except (ValueError, KeyError, TypeError): continue
if not cases:
    print('NO_CASE: reproduce failure then rerun; no state was changed')
    raise SystemExit(0)
probe = r'''
import json, os, urllib.request, urllib.parse, urllib.error
cases = json.loads(os.environ['RBAC_PROBE_CASES'])
base = os.environ.get('ENTERPRISE_RBAC_API_URL') or os.environ.get('ENTERPRISE_API_URL', '')
secret = os.environ.get('ENTERPRISE_API_SECRET_KEY', '')
if not base.startswith(('http://','https://')) or not secret:
    print('PROBE_CONFIG_MISSING'); raise SystemExit(0)
for c in cases:
    tenant, account, app = c['tenant_id'], c['account_id'], c['resource_id']
    print('CASE', 'tenant='+tenant, 'account='+account, 'app='+app)
    def get(path, params):
        url = base.rstrip('/')+'/rbac/'+path+'?'+urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={'Enterprise-Api-Secret-Key':secret,
              'X-Inner-Tenant-Id':tenant, 'X-Inner-Account-Id':account})
        try:
            with urllib.request.urlopen(req, timeout=8) as response: return json.load(response)
        except urllib.error.HTTPError as e:
            print('GET', path, 'HTTP', e.code); return None
        except Exception as e:
            print('GET', path, type(e).__name__); return None
    w = get('apps/whitelist', {'app_id':app})
    if isinstance(w, dict):
        ids = w.get('account_ids') or []
        print('WHITELIST', 'has_account='+str(account in ids), 'count='+str(len(ids)))
    p = get('apps/user-access-policies', {'app_id':app})
    if isinstance(p, dict):
        rows = p.get('data') or []
        own = [x for x in rows if (x.get('account') or {}).get('account_id') == account]
        policies = [z.get('id') for x in own for z in (x.get('access_policies') or [])]
        print('RESOURCE_POLICIES', 'scope='+str(p.get('scope')), 'rows='+str(len(rows)),
              'target_rows='+str(len(own)), 'target_policies='+str(policies[:12]),
              'pagination_present='+str('pagination' in p))
    roles = get('members/rbac-roles', {'account_id':account})
    if isinstance(roles, dict):
        rr = roles.get('roles') or []
        print('MEMBER_ROLES', 'count='+str(len(rr)))
        for role in rr[:4]:
            detail = get('roles/item', {'id':role['id']})
            if isinstance(detail, dict):
                keys = detail.get('permission_keys') or []
                print('ROLE', role['id'], 'tag='+str(detail.get('role_tag')),
                      'keys='+str([k for k in keys if k == 'agent.manage' or k.startswith('app.')]))
'''
r = subprocess.run(compose + ['exec','-T','-e','RBAC_PROBE_CASES='+json.dumps(cases),'api','python','-'],
                   input=probe, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=120)
print(r.stdout[:16000], end='')
if r.returncode: print('PROBE_EXIT', r.returncode, '(stderr omitted to avoid exposing credentials)')
PY

# 3. 补齐上轮未回传的公共创建服务与邀请流程证据（仅打印有关调用；最多 24 行）
docker-compose exec -T api python - <<'PY'
import ast, pathlib
checks = [('services/app_service.py','create_app'), ('services/account_service.py','invite_new_member')]
keys = ['try_sync_creator_access_policy_member_bindings', 'replace_whitelist',
        'initialize_created_app_rbac_access_task', 'MemberRoles.replace',
        'create_tenant_member', 'tenant_join_role', 'role_ids=']
for rel, name in checks:
    p = pathlib.Path('/app/api') / rel
    if not p.is_file():
        print(rel, 'SOURCE_NOT_AVAILABLE'); continue
    source = p.read_text(); lines = source.splitlines()
    for n in ast.walk(ast.parse(source)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            print(rel, name)
            hits = [(i+1, lines[i].strip()) for i in range(n.lineno-1, n.end_lineno)
                    if any(k in lines[i] for k in keys)]
            for i, text in hits[:10]: print(str(i)+': '+text)
PY
