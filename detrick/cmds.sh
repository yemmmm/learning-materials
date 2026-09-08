#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08 17:41
# Context: WebApp POST access-mode public返回401；已确认app/workspace/account及成员normal。同时间有whitelist关键词，核对本app有效资源权限，不改成员角色。
# Cmds: 2 条
# 已固定本次app和账号；直接在同一环境当前终端粘贴。只读查询，不修改WebApp访问范围或授权。

# 1. 当前账号RBAC角色、目标app白名单和个人策略（输出不包含账号姓名/凭据）。
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
r=call("members/rbac-roles",{"account_id":A})
if isinstance(r,dict):
 roles=r.get("roles",[]);print("member_roles="+str(len(roles)))
 for x in roles[:8]:print(json.dumps({"role_id":x.get("id"),"role_tag":x.get("role_tag"),"permission_keys":x.get("permission_keys",[])},ensure_ascii=True))
r=call("apps/whitelist",{"app_id":APP})
if isinstance(r,dict):print(json.dumps({"whitelist_count":len(r.get("account_ids") or []),"has_account":A in (r.get("account_ids") or [])}))
r=call("apps/user-access-policies",{"app_id":APP})
if isinstance(r,dict):
 rows=r.get("data") or [];target=[v for v in rows if (v.get("account") or {}).get("account_id")==A]
 print(json.dumps({"scope":r.get("scope"),"response_rows":len(rows),"target_rows_in_response":len(target),"pagination_present":bool(r.get("pagination"))}))
 for v in target[:2]:print(json.dumps({"target_policy_ids":[p.get("id") for p in (v.get("access_policies") or [])]},ensure_ascii=True))
PY

# 2. 对同一账号/app执行“查看”和“发布版本”权限检查。POST check-access只做判定，不授予权限；不代表enterprise端实际采用相同scene。
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
for scene in ("app_view_layout","app_release_and_version"):
 r=call("check-access",payload={"tenant_id":T,"account_id":A,"resource_type":"app","resource_id":APP,"scene":scene})
 if isinstance(r,dict):print(json.dumps({"diagnostic_scene":scene,"allowed":r.get("allowed","MISSING")}))
print("NOTE These are explicit diagnostic checks, not the failed enterprise POST itself")
PY
