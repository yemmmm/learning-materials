#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 22:32
# Context: 3.12.1 Agent 在 Studio 可见但不可查看/编辑；新成员加入 workspace 无旧资源权限。核对创建/入组授权入口与 app_rbac 消费；本轮只读，不执行回填或迁移。
# Cmds: 3 条
# 在服务器 Compose 目录执行。先让受影响成员各复现一次 Agent 打开失败、旧工作流打开失败。

# 1. 镜像、有效 RBAC 开关及 worker 实际订阅队列（不输出连接串或密钥；最多 20 行）
python3 - <<'PY'
import json, subprocess
def run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=25)
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

# 2. 读取运行镜像源码，比较 Agent/普通应用创建及成员入组入口（不导入业务模块、不写数据库；最多 25 行）
docker-compose exec -T api python - <<'PY'
import ast, pathlib
checks = [
 ('controllers/console/agent/roster.py', 'post', 'mode="agent"'),
 ('controllers/console/app/app.py', 'post', 'app_service.create_app'),
 ('services/app_service.py', 'create_app', ''),
 ('services/account_service.py', 'invite_new_member', ''),
 ('services/account_service.py', 'create_tenant_member', ''),
 ('controllers/console/agent/composer.py', 'put', 'save_agent_composer'),
]
keys = ['create_app', 'try_sync_creator_access_policy_member_bindings', 'replace_whitelist',
        'initialize_created_app_rbac_access_task', 'MemberRoles.replace', 'AGENT_MANAGE', 'APP_EDIT']
for rel, name, marker in checks:
    p = pathlib.Path('/app/api') / rel
    if not p.is_file():
        print(rel, 'SOURCE_NOT_AVAILABLE'); continue
    try:
        source = p.read_text(); tree = ast.parse(source)
        matches = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                part = ast.get_source_segment(source, node) or ''
                if marker and marker not in part: continue
                decorators = ' '.join(ast.unparse(x) for x in node.decorator_list)
                hits = [k for k in keys if k in part + decorators]
                matches.append(str(node.lineno)+': '+','.join(hits))
        print(rel, name, ' | '.join(matches[:3]) or 'NO_MATCH')
    except (SyntaxError, UnicodeError): print(rel, 'SOURCE_UNREADABLE')
PY

# 3. 复现后的授权拒绝与初始化任务结果（近 10 分钟，每类最多 12 行；保留 scene/role/resource 便于关联）
for svc in dify-enterprise-rbac worker; do
  echo "[$svc recent authorization evidence]"
  docker-compose logs --since 10m --tail=600 --no-color "$svc" 2>&1 |
    grep -iE 'check-access denied|initialize_created_app_rbac_access_task|Failed to initialize app RBAC|Received unregistered task.*rbac' |
    sed -E 's/((token|password|secret|authorization)[" ]*[:=][" ]*)[^ ,}]+/\1[REDACTED_SECRET]/Ig' |
    tail -12 | cut -c1-1800
done
