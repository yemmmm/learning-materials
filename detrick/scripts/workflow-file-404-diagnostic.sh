#!/bin/bash
# === Detrick Troubleshoot Round ===
# Status 2026-09-20: 本轮已回传，两路 200 且用户确认可下载；无需重复。后续查文件变量、提取与模型输入。
# Time: 2026-09-20 11:13
# Context: 工作流上传后 LLM input 文件 URL 返回 404；区分外部路由与 API 文件读取失败，根因未确认。
# Cmds: 2 条；在服务器 Compose 目录的原 shell 逐块粘贴（docker-compose 可能是函数）。
# 只读；先重新上传并运行，使用本次新生成的完整 URL。URL 仅在现场输入，不回传签名。

# 1. 核对 API 镜像、文件配置及挂载；URL 隐去主机、凭据与查询参数，最多 20 行。
# 参数行：服务名不是 api 时先修改这一行；不使用 read，整块粘贴不会吞后续命令。
DTR_FILE_API='api'
DTR_FILE_CIDS=$(docker-compose ps -q "$DTR_FILE_API")
if [ -n "$DTR_FILE_CIDS" ]; then
  docker inspect $DTR_FILE_CIDS | python -c '
import sys,json
from urllib.parse import urlsplit
for c in json.load(sys.stdin)[:3]:
 print("image="+c["Config"]["Image"].rsplit("/",1)[-1])
 env=dict(x.split("=",1) for x in c["Config"].get("Env",[]) if "=" in x)
 origins={}
 for k in ("FILES_URL","INTERNAL_FILES_URL","STORAGE_TYPE","OPENDAL_SCHEME","OPENDAL_FS_ROOT"):
  v=env.get(k,"")
  if k.endswith("URL") and v:
   p=urlsplit(v); origin=(p.scheme,p.netloc)
   if origin not in origins: origins[origin]=len(origins)+1
   v="scheme=%s origin_group=%s path=%s"%(p.scheme or "MISSING",origins[origin],p.path or "/")
  print(k+"="+(v or "UNSET_OR_EMPTY"))
 print("mount_targets="+",".join(m["Destination"] for m in c.get("Mounts",[])))
' 2>&1 | head -20
else
  echo 'NO_API_CONTAINER: check service name and Compose directory'
fi

# 2. 对同一条新链接执行有超时的 GET：原地址 vs API 容器本机端口；不打印 URL、签名或文件正文，最多 15 行。
# 参数行：先将单引号内占位文字替换为本次完整 URL，保留单引号。
DTR_FILE_URL='替换为本次新生成的完整文件URL'
docker-compose exec -T -e DTR_FILE_URL="$DTR_FILE_URL" "$DTR_FILE_API" python - <<'PY' 2>&1 | head -15
import os,re,time
from urllib.parse import urlsplit,parse_qs,urlunsplit
import requests
p=urlsplit(os.environ.get('DTR_FILE_URL',''))
if p.scheme not in ('http','https') or not p.netloc:
    print('INVALID_URL: paste the complete http(s) URL'); raise SystemExit
safe_path=re.sub(r'[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}', '<file-id>', p.path)
print('path='+safe_path)
q=parse_qs(p.query)
print('signature_fields='+','.join(k for k in ('timestamp','nonce','sign') if k in q))
try: print('timestamp_age_seconds='+str(int(time.time())-int(q['timestamp'][0])))
except (KeyError,ValueError): print('timestamp_age_seconds=UNKNOWN')
port=os.getenv('DIFY_PORT') or '5001'
direct=urlunsplit(('http','127.0.0.1:'+port,p.path,p.query,''))
for label,url in [('original_from_api',p.geturl()),('direct_api',direct)]:
    session=requests.Session()
    if label=='direct_api': session.trust_env=False
    try:
        with session.get(url,timeout=(5,10),stream=True,allow_redirects=False) as r:
            print('%s status=%s content_type=%s redirect=%s'%(label,r.status_code,r.headers.get('Content-Type',''),bool(r.headers.get('Location'))))
            if r.status_code>=400:
                body=next(r.iter_content(2048),b'').decode('utf-8','replace').lower()
                markers=[s for s in ('file not found','invalid signature','signature expired','not found','<!doctype html','<html') if s in body]
                print(label+' error_markers='+','.join(markers))
    except requests.RequestException as e:
        print(label+' error_type='+type(e).__name__)
    finally: session.close()
PY
unset DTR_FILE_URL
