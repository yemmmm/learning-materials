#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08
# Context: 本次WebApp权限修改401已修复；以下保留只读配置对照。其他环境修复步骤见webapp-access-mode-diagnosis.md，完整修复命令见41e5a08版本。
# Cmds: 2 条
# 在刚才执行失败命令的同一终端、同一目录粘贴；本轮只读，不重建服务，不输出完整环境/Compose。

# 1. 读取当前目录、运行容器RBAC值及创建时的Compose文件标签。最多4行；标签记录的是创建时文件，不保证等于这次调用。
docker inspect $(docker-compose ps -q) | python3 -c '
import os,sys,json
rows=json.load(sys.stdin)
print(json.dumps({"shell_cwd":os.getcwd(),"shell_COMPOSE_FILE":os.environ.get("COMPOSE_FILE","UNSET")}))
selected=[]
for r in rows:
 c=r.get("Config") or {};l=c.get("Labels") or {}
 image=c.get("Image","").split("@",1)[0].rsplit("/",1)[-1].split(":",1)[0]
 if l.get("com.docker.compose.service")=="api" or image=="dify-ee-enterprise":selected.append(r)
if not selected:print("NO_API_OR_ENTERPRISE_CONTAINER")
for r in selected[:3]:
 c=r["Config"];l=c.get("Labels") or {};e=dict(x.split("=",1) for x in c.get("Env",[]) if "=" in x)
 print(json.dumps({"source":"running_container","service":l.get("com.docker.compose.service"),"rbac_present":"RBAC_ENABLED" in e,"rbac_value":repr(e.get("RBAC_ENABLED"))[:80],"created_with_workdir":l.get("com.docker.compose.project.working_dir"),"created_with_files":l.get("com.docker.compose.project.config_files")},ensure_ascii=True))
'

# 2. 原样展示当前Compose解析后的RBAC值和类型，便于区分未设置、false、空值、额外引号或空格。最多4行。
docker-compose config 2>/dev/null | docker-compose exec -T api python -c '
import sys,json
try:
 import yaml
 d=yaml.safe_load(sys.stdin)
 if not isinstance(d,dict) or not isinstance(d.get("services"),dict):print("CONFIG_UNAVAILABLE");sys.exit(1)
 rows=[]
 for name,c in d["services"].items():
  image=str(c.get("image","")).split("@",1)[0].rsplit("/",1)[-1].split(":",1)[0]
  if name!="api" and image!="dify-ee-enterprise":continue
  env=c.get("environment") or {};kind=type(env).__name__
  if isinstance(env,list):env=dict((x.split("=",1)+[None])[:2] for x in env)
  value=env.get("RBAC_ENABLED")
  row={"source":"compose_resolved","service":name,"environment_type":kind,"rbac_present":"RBAC_ENABLED" in env,"rbac_value":repr(value)[:80],"rbac_type":type(value).__name__,"passes_previous_check":str(value).lower() in ("true","1")}
  rows.append(row)
 print(json.dumps({"selected_services":len(rows)}))
 for row in rows[:3]:print(json.dumps(row,ensure_ascii=True))
except Exception as e:print("CONFIG_READ_FAILED="+type(e).__name__);sys.exit(1)
'
