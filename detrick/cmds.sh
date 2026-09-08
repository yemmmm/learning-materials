#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08 16:58
# Context: 上轮CHUNKS_NOT_FOUND只说明预设静态目录不适用。先获取web实际目录，再有限深度自动发现嵌套chunks并核对转换代码。
# Cmds: 2 条
# 同一终端逐块粘贴；只读，不重启、不改工作流/配置。命令2有扫描上限，找不到也不代表代码不存在。

# 1. 镜像、配置工作目录以及Node当前目录/PID1目录；仅输出路径，最多18行。
docker inspect $(docker-compose ps -q web) | python3 -c '
import json,sys
for r in json.load(sys.stdin):
 c=r.get("Config",{});print("image="+c.get("Image",""));print("workdir="+c.get("WorkingDir",""))
' | head -6
docker-compose exec -T web node - <<'JS'
const fs=require('node:fs');
console.log('node_cwd='+process.cwd());
try{console.log('pid1_cwd='+fs.readlinkSync('/proc/1/cwd'))}catch{console.log('pid1_cwd=unavailable')}
try{console.log('cwd_dirs='+fs.readdirSync(process.cwd(),{withFileTypes:true}).filter(e=>e.isDirectory()).map(e=>e.name).slice(0,12).join(','))}catch{console.log('cwd_dirs=unavailable')}
JS

# 2. 在应用目录等有限范围自动查找，深度<=6/目录<=1200；扫描JS<=2500个，最多3个候选代码片段。
docker-compose exec -T web node - <<'JS'
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
let initCwd='';try{initCwd=fs.readlinkSync('/proc/1/cwd')}catch{}
const seeds=[process.cwd(),initCwd,'/app','/opt','/srv','/usr/src/app','/usr/share/nginx/html','/workspace','/var/www'].filter(x=>x&&x!=='/');
const queue=seeds.map(p=>[p,0]),seen=new Set(),chunkRoots=new Set();let checked=0;
while(queue.length&&checked<1200&&chunkRoots.size<4){
 const [dir,depth]=queue.shift();let real;
 try{real=fs.realpathSync(dir)}catch{continue}
 if(seen.has(real))continue;seen.add(real);checked++;
 for(const candidate of [path.join(dir,'.next/static/chunks'),path.join(dir,'static/chunks')]){
  try{if(fs.statSync(candidate).isDirectory())chunkRoots.add(fs.realpathSync(candidate))}catch{}
 }
 if(depth>=6)continue;
 let entries;try{entries=fs.readdirSync(dir,{withFileTypes:true})}catch{continue}
 for(const e of entries){
  if(!e.isDirectory()||['node_modules','.git','cache','.cache','certs','certificates','ca-certificates'].includes(e.name))continue;
  queue.push([path.join(dir,e.name),depth+1]);
 }
}
console.log('discovery_dirs='+checked+' chunk_roots='+chunkRoots.size);
for(const r of chunkRoots)console.log('CHUNKS '+r);
if(!chunkRoots.size){console.log('NOT_FOUND within bounded search; report command 1 paths');process.exit(0)}
let visited=0,hits=0,skipped=0;const todo=[...chunkRoots],scannedDirs=new Set();
while(todo.length&&visited<2500&&hits<3){
 const dir=todo.pop();if(scannedDirs.has(dir))continue;scannedDirs.add(dir);
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
