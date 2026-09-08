#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08 16:53
# Context: 刷新复发；参考协同初始化把Completion对象转换成[]，本地已复现。只读核对线上web镜像及编译包是否包含同样转换。
# Cmds: 2 条
# 在同一受影响环境当前终端逐块粘贴；不重启、不改配置、不操作工作流。

# 1. 实际web镜像和挂载目标（挂载源不输出），最多8行。
docker inspect $(docker-compose ps -q web) | python3 -c '
import json,sys
for r in json.load(sys.stdin):
 print("image="+r.get("Config",{}).get("Image",""))
 print("image_id="+r.get("Image",""))
 print("mount_targets="+json.dumps([m.get("Destination") for m in r.get("Mounts",[])]))
' | head -8

# 2. 扫描已部署前端静态JS，最多3个候选、11行；仅输出字段列表及附近转换代码，不读取业务数据。
docker-compose exec -T web node - <<'JS'
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const roots=[path.join(process.cwd(),'.next/static/chunks'),'/app/web/.next/static/chunks','/app/.next/static/chunks'];
const root=roots.find(p=>fs.existsSync(p));
if(!root){console.log('CHUNKS_NOT_FOUND');process.exit(0)}
let visited=0,hits=0,skipped=0;const todo=[root];
while(todo.length&&visited<2500&&hits<3){
 const dir=todo.pop();
 for(const e of fs.readdirSync(dir,{withFileTypes:true})){
  const p=path.join(dir,e.name);
  if(e.isDirectory()){todo.push(p);continue}
  if(!e.isFile()||!e.name.endsWith('.js'))continue;
  if(visited>=2500||hits>=3)break;
  visited++;
  if(fs.statSync(p).size>20*1024*1024){skipped++;continue}
  const s=fs.readFileSync(p,'utf8');
  const re=/new Set\s*\(\s*\[([^\]]{0,240})\]\s*\)/g;let m;
  while((m=re.exec(s))){
   if(!['prompt_template','variables','parameters'].every(k=>m[1].includes(k)))continue;
   hits++;
   console.log('FILE '+path.basename(p)+' sha256='+crypto.createHash('sha256').update(s).digest('hex').slice(0,16));
   console.log('LIST_FIELDS '+m[0].replace(/\s+/g,' ').slice(0,200));
   const segment=s.slice(m.index,m.index+3500);const i=segment.indexOf('Array.isArray');
   console.log('CONVERSION '+(i<0?'not found nearby':segment.slice(Math.max(0,i-50),i+150).replace(/\s+/g,' ')));
   break;
  }
 }
}
console.log('scanned='+visited+' candidates='+hits+' skipped_large='+skipped);
if(!hits)console.log('NO_MATCH does not prove absence; minification/version/path may differ');
JS
