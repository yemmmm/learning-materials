#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-09
# Context: 10缺少额外CA/代理配置，11有；10直连证书失败，11直连DNS失败。验证10现有CA文件是否足够。
# Cmds: 3 条；在原Compose目录、原shell逐块粘贴。命令1/2两台执行；命令3只在10执行。
# 只读；临时Node子进程使用额外CA，不改运行worker、不重启、不发送HTTP请求。

# 1. 输入本机受测worker服务与同一个失败HTTPS目标；不要填n8n入口域名（除非原节点就是请求它）。
read -r -p 'Worker Compose service: ' DTR_WORKER
read -r -p 'Failing HTTPS hostname (no URL/path): ' DTR_TLS_HOST
read -r -p 'HTTPS port [443]: ' DTR_TLS_PORT
DTR_TLS_PORT=${DTR_TLS_PORT:-443}

# 2. 两台分别查看受测worker的实际证书挂载来源，最多20行；回传前遮盖目录中的内部标识。
DTR_WORKER_CID=$(docker-compose ps -q "$DTR_WORKER")
if [ -n "$DTR_WORKER_CID" ]; then
  docker inspect --format '{{range .Mounts}}{{println .Type .Source "->" .Destination "rw=" .RW}}{{end}}' "$DTR_WORKER_CID" 2>&1 | head -20
else
  echo 'Worker container not found; check service name'
fi

# 3. 仅10执行：相同目标分别用原环境/显式加载现有CA文件进行严格直连TLS验证；最多20行，总计约24秒超时。
# 不经过HTTP代理，不覆盖节点自定义CA/代理，也不替代原工作流验收。
docker-compose exec -T "$DTR_WORKER" node - "$DTR_TLS_HOST" "$DTR_TLS_PORT" <<'JS' 2>&1 | head -20
const fs=require('fs'),cp=require('child_process');let env;
for(const id of fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x))){try{
  const cmd=fs.readFileSync('/proc/'+id+'/cmdline','utf8').split('\0');
  if(cmd.some(x=>/(^|\/)n8n$/.test(x))&&cmd.includes('worker')){env=Object.fromEntries(fs.readFileSync('/proc/'+id+'/environ','utf8').split('\0').filter(Boolean).map(x=>{const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1)]}));break;}
}catch{}}
if(!env){console.log('SKIP: runtime worker environment not found; return command 2 output');process.exit(1)}
const host=process.argv[2],port=Number(process.argv[3]);
if(!host||/[:/\s@]/.test(host)||!Number.isInteger(port)||port<1||port>65535){console.log('INPUT_ERROR: hostname only, port 1..65535');process.exit(1)}
const code=`const tls=require('tls');const s=tls.connect({host:process.argv[1],port:Number(process.argv[2]),servername:process.argv[1],rejectUnauthorized:true},()=>{console.log('TLS=OK authorized='+s.authorized);s.destroy()});s.on('error',e=>{console.log('TLS=FAIL code='+e.code);process.exitCode=1});setTimeout(()=>{console.log('TLS=TIMEOUT');s.destroy();process.exit(2)},10000).unref();`;
for(const mode of ['baseline','existing_CA_bundle']){
  const testEnv={...env};if(mode==='existing_CA_bundle')testEnv.NODE_EXTRA_CA_CERTS='/etc/ssl/certs/ca-certificates.crt';
  const r=cp.spawnSync(process.execPath,['-e',code,host,String(port)],{env:testEnv,encoding:'utf8',timeout:12000});
  console.log('mode='+mode);process.stdout.write(r.stdout||'');
  if(r.error)console.log('probe_error='+r.error.code);
  if(r.status!==0&&!(r.stdout||''))console.log('probe_exit='+r.status+'; startup failed');
  if(r.stderr)console.log('startup_stderr_present=true');
}
JS
