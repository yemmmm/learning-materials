#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-09
# Context: n8n分布式worker对相同HTTPS目标的CA信任差异；尚未确认根因。
# Cmds: 3 条；分别在两台机器的原Compose目录、当前shell中逐块粘贴执行。
# 不修改配置、不重启服务；仅TLS握手，不发送HTTP请求或凭据。
# 目标填失败HTTP Request最终访问的HTTPS主机名；若发生重定向，填实际失败的主机。

# 1. 查看服务名并输入本机worker服务、相同目标域名和端口；最多20行。
docker-compose config --services 2>&1 | head -20
read -r -p 'Worker Compose service: ' DTR_WORKER
read -r -p 'Failing HTTPS hostname (no URL/path): ' DTR_TLS_HOST
read -r -p 'HTTPS port [443]: ' DTR_TLS_PORT
DTR_TLS_PORT=${DTR_TLS_PORT:-443}

# 2. 比较版本及运行中worker的CA设置；只显示指定字段，证书仅输出摘要，最多30行。
docker-compose exec -T "$DTR_WORKER" sh -c 'n8n --version; node' <<'JS' 2>&1 | head -30
const fs=require('fs'), crypto=require('crypto');
console.log('node='+process.version);
let env;
for(const id of fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x))){
  try{const cmd=fs.readFileSync('/proc/'+id+'/cmdline','utf8').split('\0');
    if(cmd.some(x=>/(^|\/)n8n$/.test(x)) && cmd.includes('worker')){
      env=Object.fromEntries(fs.readFileSync('/proc/'+id+'/environ','utf8').split('\0').filter(Boolean).map(x=>{const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1)]}));break;
    }
  }catch{}
}
console.log('runtime_worker_env='+(env?'FOUND':'NOT_FOUND')); env=env||process.env;
for(const k of ['NODE_EXTRA_CA_CERTS','SSL_CERT_FILE','SSL_CERT_DIR','NODE_USE_SYSTEM_CA','NODE_TLS_REJECT_UNAUTHORIZED']) console.log(k+'='+(env[k]||'UNSET'));
console.log('CA_flags='+((env.NODE_OPTIONS||'').match(/--use-(system|openssl|bundled)-ca/g)||[]).join(','));
for(const k of ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy']) console.log(k+'='+(env[k]?'SET':'UNSET'));
const files=new Set([env.NODE_EXTRA_CA_CERTS,env.SSL_CERT_FILE,'/etc/ssl/certs/ca-certificates.crt'].filter(Boolean));
try{const a=fs.readdirSync('/opt/custom-certificates').filter(x=>/\.(pem|crt|cer)$/.test(x));console.log('custom_CA_files='+a.length);for(const n of a.slice(0,4)) files.add('/opt/custom-certificates/'+n)}catch(e){console.log('custom_CA_dir='+e.code)}
for(const f of files){try{const b=fs.readFileSync(f);console.log('CA '+f+' pem_count='+((b.toString().match(/BEGIN CERTIFICATE/g)||[]).length)+' sha256='+crypto.createHash('sha256').update(b).digest('hex'))}catch(e){console.log('CA '+f+' '+e.code)}}
JS

# 3. 使用运行中worker环境启动Node进行严格TLS验证，12秒超时，最多15行；直连，不经过HTTP代理。
# 此探针不覆盖节点单独指定的CA/代理；成功不能替代原工作流复测。
docker-compose exec -T "$DTR_WORKER" node - "$DTR_TLS_HOST" "$DTR_TLS_PORT" <<'JS' 2>&1 | head -15
const fs=require('fs'),cp=require('child_process');let env;
for(const id of fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x))){try{
  const cmd=fs.readFileSync('/proc/'+id+'/cmdline','utf8').split('\0');
  if(cmd.some(x=>/(^|\/)n8n$/.test(x))&&cmd.includes('worker')){env=Object.fromEntries(fs.readFileSync('/proc/'+id+'/environ','utf8').split('\0').filter(Boolean).map(x=>{const i=x.indexOf('=');return [x.slice(0,i),x.slice(i+1)]}));break;}
}catch{}}
if(!env){console.log('SKIP: runtime worker environment not found; return command 2 output');process.exit(1)}
const host=process.argv[2],port=Number(process.argv[3]);
if(!host||/[:/\s@]/.test(host)||!Number.isInteger(port)||port<1||port>65535){console.log('INPUT_ERROR: hostname only, port 1..65535');process.exit(1)}
const code=`const tls=require('tls');const s=tls.connect({host:process.argv[1],port:Number(process.argv[2]),servername:process.argv[1],rejectUnauthorized:true},()=>{console.log('TLS=OK authorized='+s.authorized);s.destroy()});s.on('error',e=>{console.log('TLS=FAIL code='+e.code);process.exitCode=1});setTimeout(()=>{console.log('TLS=TIMEOUT');s.destroy();process.exit(2)},10000).unref();`;
const r=cp.spawnSync(process.execPath,['-e',code,host,String(port)],{env,encoding:'utf8',timeout:12000});
process.stdout.write(r.stdout||'');if(r.error)console.log('probe_error='+r.error.code);if(r.status!==0&&!(r.stdout||''))console.log('probe_exit='+r.status+'; startup failed; inspect NODE_OPTIONS');
JS
