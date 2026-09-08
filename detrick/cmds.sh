#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08
# Context: 目标app白名单含账号/default策略，查看和发布check-access通过；Enterprise POST仍ErrUnauthorized。核对独立访问配置权限及Enterprise RBAC路由。
# Cmds: 2 条
# 在原部署目录、当前已定义docker-compose函数的终端分别粘贴。只读，不修改访问范围。

# 1. 检查独立的app_access_config权限；诊断调用不等于原POST实际使用的scene。输出最多3行。
docker-compose exec -T api python - <<'PY'
import os,json,urllib.request,urllib.parse,urllib.error,sys
T="a5bcd310-2e74-4f89-9a32-70a56694cb35"
A="dc81582c-3934-4d8f-b034-9cb7809dce2b"
APP="daeaaeb3-6875-4f73-adad-0f1312dbd5ce"
root=os.environ.get("ENTERPRISE_RBAC_API_URL","").rstrip("/")
secret=os.environ.get("ENTERPRISE_API_SECRET_KEY","")
if not root or not secret:print("RBAC_URL_OR_SECRET_UNSET");sys.exit(1)
headers={"Enterprise-Api-Secret-Key":secret,"X-Inner-Tenant-Id":T,"X-Inner-Account-Id":A,"Content-Type":"application/json"}
def call(path,params=None,payload=None):
 url=root+"/rbac/"+path
 if params:url+="?"+urllib.parse.urlencode(params)
 req=urllib.request.Request(url,data=json.dumps(payload).encode() if payload is not None else None,headers=headers,method="POST" if payload is not None else "GET")
 try:
  with urllib.request.urlopen(req,timeout=10) as res:return json.load(res)
 except urllib.error.HTTPError as e:print(path+" HTTP="+str(e.code))
 except Exception as e:print(path+" FAILED="+type(e).__name__)
 return None
for scene in ("app_access_config",):
 r=call("check-access",payload={"tenant_id":T,"account_id":A,"resource_type":"app","resource_id":APP,"scene":scene})
 if isinstance(r,dict):print(json.dumps({"diagnostic_scene":scene,"allowed":r.get("allowed","MISSING")}))
print("NOTE These are explicit diagnostic checks, not the failed enterprise POST itself")
PY

# 2. 比较API和Enterprise的RBAC目标及内部密钥，仅输出相等/配置状态，不输出密钥或内部主机。最多8行。
docker inspect $(docker-compose ps -q api dify-enterprise) | python3 -c '
import sys,json
from urllib.parse import urlsplit
rows=json.load(sys.stdin); services={}
for row in rows:
 cfg=row.get("Config") or {}; service=(cfg.get("Labels") or {}).get("com.docker.compose.service")
 if service in ("api","dify-enterprise"):
  services.setdefault(service,[]).append(dict(x.split("=",1) for x in (cfg.get("Env") or []) if "=" in x))
if any(len(services.get(k,[]))!=1 for k in ("api","dify-enterprise")):
 print("EXPECTED_ONE_API_AND_ONE_ENTERPRISE");sys.exit(1)
a=services["api"][0];e=services["dify-enterprise"][0]
x=a.get("ENTERPRISE_RBAC_API_URL","");y=e.get("RBAC_INNER_BASE_URL","")
def shape(label,value):
 u=urlsplit(value);print(json.dumps({"target":label,"set":bool(value),"scheme":u.scheme,"path":u.path}))
shape("api.ENTERPRISE_RBAC_API_URL",x);shape("enterprise.RBAC_INNER_BASE_URL",y)
u=urlsplit(x);v=urlsplit(y)
print("rbac_same_origin="+str(bool(x and y) and (u.scheme,u.hostname,u.port)==(v.scheme,v.hostname,v.port)))
k="ENTERPRISE_API_SECRET_KEY"
print("inner_secret="+("EQUAL" if a.get(k) and a.get(k)==e.get(k) else "MISSING_OR_DIFFERENT"))
for k in ("WEBAPP_PUBLIC_ACCESS_ENABLED",):
 value=e.get(k);print("enterprise."+k+"="+(value if value in ("true","false","True","False","1","0") else "UNSET" if value is None else "OTHER_VALUE"))
'
