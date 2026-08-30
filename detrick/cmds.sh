#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-30 23:04
# Context: 容器内存在 HTTP_PROXY/HTTPS_PROXY=122.200.106.5:8080 且 NO_PROXY 不含 minio，怀疑 n8n 的 S3 请求被代理劫持（代理无法解析 docker 域名 minio）。本轮对照实验：带代理与清掉代理各发一次 HeadBucket
# Cmds: 2 条

# 1. 先把 S3 测试脚本写进容器 /tmp/s3test.js 再执行（避免长命令粘贴被截断）。当前环境（带代理）跑一次，输出 OK 或 ERR+错误码
docker-compose exec -T n8n-main-1 sh -c 'cat > /tmp/s3test.js << "JSEOF"
const { S3Client, HeadBucketCommand } = require("@aws-sdk/client-s3");
const c = new S3Client({ region: process.env.N8N_EXTERNAL_STORAGE_S3_BUCKET_REGION, endpoint: process.env.N8N_EXTERNAL_STORAGE_S3_ENDPOINT, forcePathStyle: true, credentials: { accessKeyId: process.env.N8N_EXTERNAL_STORAGE_S3_ACCESS_KEY, secretAccessKey: process.env.N8N_EXTERNAL_STORAGE_S3_ACCESS_SECRET } });
c.send(new HeadBucketCommand({ Bucket: process.env.N8N_EXTERNAL_STORAGE_S3_BUCKET_NAME })).then(r => console.log("WITH-PROXY OK", r.$metadata.httpStatusCode)).catch(e => console.log("WITH-PROXY ERR", e.name, e.$metadata && e.$metadata.httpStatusCode, String(e.message).slice(0, 150)));
JSEOF
NODE_PATH=/usr/local/lib/node_modules/n8n/node_modules node /tmp/s3test.js' 2>&1 | tail -3

# 2. 清空代理环境变量后用同一脚本再跑一次（若这次 OK 而上一条 ERR，即证明代理是根因）
docker-compose exec -T n8n-main-1 sh -c 'NODE_PATH=/usr/local/lib/node_modules/n8n/node_modules HTTP_PROXY= HTTPS_PROXY= http_proxy= https_proxy= node /tmp/s3test.js' 2>&1 | tail -3
