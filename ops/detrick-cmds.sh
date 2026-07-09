#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-09 14:00
# Context: minio 数据被误删后 api 报"租户找不到 privkey"，用户手动在 difyai/privkeys/ 下放了一个 xxxxx.pem 但 api 仍报同样错。本轮要确认三件事：① 报错日志原文 + 涉及的具体 tenant_id；② minio 里 privkeys 目录下实际的文件名（是否和 tenant_id 一致）；③ api 的存储配置（bucket 名/endpoint/路径前缀）
# Cmds: 3 条

# 1. 抓 api 最近 300 行日志中和 privkey/tenant 相关的报错原文 —— 重点看 "tenant_id=xxx" 和 "xxx.pem" 这两个关键信息
docker-compose logs --tail=300 api 2>&1 | grep -iE 'privkey|private.*key|tenant|decrypt|rsa|\.pem|not.*found|no such' | tail -30

# 2. 列出 minio 宿主机卷里 difyai/privkeys/ 下实际有哪些文件 —— 文件名必须严格等于 <tenant_id>.pem，多了下划线/UUID 后缀都会让 api 找不到
ls -la volumes/minio/data/difyai/privkeys/ 2>&1 | head -20

# 3. 看 api 的存储配置（STORAGE_TYPE / S3 bucket / endpoint / 路径前缀 PATH）—— 确认 api 真的是去 difyai/privkeys/ 找而不是别的 bucket
docker-compose exec -T api env 2>&1 | grep -iE 'STORAGE_TYPE|S3_|MINIO_|BUCKET|STORAGE_LOCAL_PATH|CONSOLE_API_URL' | head -20
