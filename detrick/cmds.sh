#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-30 22:59
# Context: endpoint/bucket/网络均已验证正常，仍 Failed to connect to S3。嫌疑集中在签名校验（region=auto 与 MinIO 默认 us-east-1 不匹配）。本轮用容器内 AWS SDK 直接发真实请求拿底层错误码
# Cmds: 2 条

# 1. 【关键】在 n8n 容器内用其自带的 @aws-sdk/client-s3 按 n8n 实际配置发 HeadBucket，打印真实错误（SignatureDoesNotMatch=region或密钥签名问题，403=凭据错，404=bucket不存在）
docker-compose exec -T n8n-main-1 sh -c 'NODE_PATH=/usr/local/lib/node_modules/n8n/node_modules node -e "const {S3Client, HeadBucketCommand} = require(\"@aws-sdk/client-s3\"); const c = new S3Client({region: process.env.N8N_EXTERNAL_STORAGE_S3_BUCKET_REGION, endpoint: process.env.N8N_EXTERNAL_STORAGE_S3_ENDPOINT, forcePathStyle: true, credentials: {accessKeyId: process.env.N8N_EXTERNAL_STORAGE_S3_ACCESS_KEY, secretAccessKey: process.env.N8N_EXTERNAL_STORAGE_S3_ACCESS_SECRET}}); c.send(new HeadBucketCommand({Bucket: process.env.N8N_EXTERNAL_STORAGE_S3_BUCKET_NAME})).then(r => console.log(\"OK\", r.$metadata.httpStatusCode)).catch(e => console.log(\"ERR\", e.name, e.$metadata && e.$metadata.httpStatusCode, String(e.message).slice(0, 200)))"' 2>&1 | tail -5

# 2. 【补测】上轮因容器重启没跑成的代理变量检查（若存在 HTTP_PROXY 会劫持 S3 请求）
docker-compose exec -T n8n-main-1 sh -c 'env | grep -iE "proxy|no_proxy" | cat -A' 2>&1 | head -10
