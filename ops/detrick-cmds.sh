#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-09 14:26
# Context: 上轮确认 minio 中 <tenant_id>.pem 文件名与 tenant_id 匹配，但 api 仍报"找不到 privkey"。本轮转向数据库——Dify 3.x 的 privkey 是双份存储（minio 文件 + tenants 表里的加密字段），需要确认 DB 这份是否还在/非空，同时区分 api 当前报错属于哪种：① 文件 not found ② decrypt/rsa failed（内容不对）③ DB 字段为 null
# Cmds: 3 条

# 1. tenants 表里所有与 privkey/加密相关的字段名（Dify 各版本字段名不一样，先拿到实际字段名，3.8.0 可能是 encrypt_key_pair/encrypted_privkey/privkey 之一）
docker-compose exec -T db_postgres psql -U postgres -d dify -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='tenants' AND (column_name ILIKE '%priv%' OR column_name ILIKE '%key%' OR column_name ILIKE '%encrypt%' OR column_name ILIKE '%rsa%')" 2>&1 | head -20

# 2. 列出所有租户的 id/name/status —— 拿 DB 里实际 tenant_id 再和 minio 里那个 .pem 文件名做最终核对（注意大小写/连字符/UUID 完整性）
docker-compose exec -T db_postgres psql -U postgres -d dify -c "SELECT id, name, status, created_at FROM tenants ORDER BY created_at DESC" 2>&1 | head -20

# 3. api 最近 30 分钟的报错原文 —— 重点区分错误类型："privkey.*not.*found"=api 没读到 minio 文件；"decrypt|rsa|invalid.*key"=读到文件但内容不对（用 AI 重生成的密钥≠原始密钥，加密过的数据无法解密）；"is null|no.*privkey"=DB 字段空
docker-compose logs --since 30m api 2>&1 | grep -iE 'priv|decrypt|rsa|pem|invalid|fail|not.*found|null' | tail -30
