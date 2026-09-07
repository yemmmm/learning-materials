#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 23:32
# Context: 对比正常/异常环境，未认定镜像缺陷。检查有效配置、RBAC 指向、API/worker 一致性、实际队列和源码指纹；全部只读。
# Cmds: 3 条
# 两套环境各自在 Compose 目录执行，并标注正常/异常及测试类型（新 Agent 或 Workflow）。
# 已定义 docker-compose() 的终端中 source ./cmds.sh，或逐条粘贴执行。

# 1. 运行镜像与有效配置；凭据只比较是否一致，不输出内容（最多 25 行）
if declare -F docker-compose >/dev/null; then export -f docker-compose; fi
python3 - <<'PY'
import json, subprocess
from urllib.parse import urlsplit
compose = ['bash','-c','docker-compose "$@"','rbac-probe']
def run(args):
    r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=25)
    if r.returncode: raise RuntimeError('command failed: '+args[0]+' exit='+str(r.returncode))
    return r.stdout
def endpoint(v):
    if not v: return '<unset>'
    try:
        u = urlsplit(v if '://' in v else '//'+v)
        return (u.scheme+'://' if u.scheme else '')+str(u.hostname)+(':'+str(u.port) if u.port else '')
    except ValueError: return '<unparseable>'
envs = {}
for svc in ['api','worker','web','dify-enterprise','dify-enterprise-rbac']:
    ids = run(compose+['ps','-q',svc]).split()
    if not ids:
        print(svc,'NO_CONTAINER'); continue
    for cid in ids[:2]:
        o = json.loads(run(['docker','inspect',cid]))[0]
        e = dict(x.split('=',1) for x in o['Config'].get('Env',[]) if '=' in x)
        if svc not in envs: envs[svc] = e
        print('IMAGE',svc,o['Config']['Image'],'id='+o['Image'],
              'code_mounts='+str([m['Destination'] for m in o.get('Mounts',[]) if m['Destination'] in ['/app','/app/api','/app/web']]))
        print('CONFIG',svc,'RBAC='+e.get('RBAC_ENABLED','<unset>'),
              'ENTERPRISE='+e.get('ENTERPRISE_ENABLED','<unset>'),
              'rbac_target='+endpoint(e.get('ENTERPRISE_RBAC_API_URL') or e.get('RBAC_INNER_BASE_URL')),
              'db_host='+endpoint(e.get('DB_HOST')),'db_name='+e.get('DB_DATABASE',e.get('DB_NAME','<unset>')))
a,w = envs.get('api',{}),envs.get('worker',{})
for group,keys in [
 ('routing',['ENTERPRISE_API_URL','ENTERPRISE_RBAC_API_URL','RBAC_ENABLED','DB_HOST','DB_PORT','DB_DATABASE','DB_USERNAME']),
 ('broker',['CELERY_BROKER_URL','CELERY_QUEUES','REDIS_HOST','REDIS_PORT','REDIS_DB','REDIS_USERNAME']),
 ('credentials',['ENTERPRISE_API_SECRET_KEY','DB_PASSWORD','REDIS_PASSWORD'])]:
    print('API_WORKER_ENV_COMPARE',group,
          ' '.join(k+':'+('both-unset' if k not in a and k not in w else 'equal' if a.get(k)==w.get(k) else 'DIFFERENT') for k in keys))
PY

# 2. 实际 Celery 队列：允许 JSON 前后有启动日志；不输出原始日志/连接串（最多 12 行）
if declare -F docker-compose >/dev/null; then export -f docker-compose; fi
python3 - <<'PY'
import json, subprocess
args=['bash','-c','docker-compose "$@"','rbac-probe','exec','-T','worker','celery','-A','app.celery','inspect','active_queues','--timeout=5','--json']
r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=45)
decoder=json.JSONDecoder(); found=None
for stream in [r.stdout,r.stderr]:
    for i,ch in enumerate(stream):
        if ch!='{': continue
        try: obj,end=decoder.raw_decode(stream[i:])
        except ValueError: continue
        if isinstance(obj,dict) and obj and all(isinstance(v,list) and all(isinstance(q,dict) and 'name' in q for q in v) for v in obj.values()):
            found=obj; break
    if found is not None: break
if found is not None:
    for worker,queues in list(found.items())[:8]:
        names=[q['name'] for q in queues]
        print('ACTIVE_QUEUE',worker,'app_rbac='+str('app_rbac' in names),'count='+str(len(names)))
else:
    merged=(r.stdout+r.stderr).lower()
    hints=[x for x in ['no nodes replied','unrecognized arguments','no such option','unable to load celery application','connection refused','authentication','timed out','not found'] if x in merged]
    print('QUEUE_UNRESOLVED','exit='+str(r.returncode),'stdout_bytes='+str(len(r.stdout)),'stderr_bytes='+str(len(r.stderr)),'hints='+str(hints))
    print('No subscription conclusion can be drawn from this result.')
PY

# 3. API/worker 的创建、邀请、初始化源码指纹（每个服务 5 行，最多 12 行；不执行业务代码）
for svc in api worker; do
  echo "[source $svc]"
  docker-compose exec -T "$svc" python - <<'PY'
import ast,hashlib,pathlib
checks=[
 ('controllers/console/agent/roster.py','post','mode="agent"'),
 ('controllers/console/app/app.py','post','app_service.create_app'),
 ('services/app_service.py','create_app',''),
 ('services/account_service.py','invite_new_member',''),
 ('tasks/initialize_created_app_rbac_access_task.py','initialize_created_app_rbac_access_task','')]
keys=['replace_whitelist','initialize_created_app_rbac_access_task.delay','MemberRoles.replace','try_sync_creator_access_policy_member_bindings']
for rel,name,marker in checks:
    p=pathlib.Path('/app/api')/rel
    if not p.is_file(): print(rel,'SOURCE_UNAVAILABLE'); continue
    raw=p.read_bytes()
    try:
        s=raw.decode(); tree=ast.parse(s); bodies=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.FunctionDef) and n.name==name:
                body=ast.get_source_segment(s,n) or ''
                if not marker or marker in body: bodies.append(body)
        text='\n'.join(bodies)
        print(rel,'sha256='+hashlib.sha256(raw).hexdigest()[:16],
              'matched='+str(len(bodies)),'calls='+','.join(k for k in keys if k in text))
    except (SyntaxError,UnicodeError): print(rel,'SOURCE_UNREADABLE')
PY
done
