#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-09
# Context: 上一轮已重生密钥对+清空 tool_* 表加密字段+重启，但仍有接口报"incorrect decryption"。核心怀疑：数据库中还有其他表/字段存着旧密钥加密的数据未被清理。本轮目标：找出所有仍含加密数据的表和字段。
# Cmds: 4 条（广撒网：找加密字段 + 查 enterprise/api 日志 + 检查密钥文件一致性）

# 1. 搜索 dify 库中所有可能包含加密数据的字段（查找列名含 encrypt/cipher/secret/credential/key 的表）
docker-compose exec -T db_postgres psql -U postgres -d dify -c "SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema='public' AND (column_name LIKE '%encrypt%' OR column_name LIKE '%cipher%' OR column_name LIKE '%secret%' OR column_name LIKE '%credential%') ORDER BY table_name, column_name;" 2>&1

# 2. 逐个检查可疑表是否有非空加密数据（看哪些表还残留旧密钥加密的字段值）
docker-compose exec -T db_postgres psql -U postgres -d dify 2>&1 <<'SQL' | head -50
SELECT 'tenant_accounts' as tbl, count(*) as encrypted_rows FROM tenant_accounts WHERE encrypted_credentials IS NOT NULL AND encrypted_credentials != ''
UNION ALL SELECT 'tenant_custom_configs', count(*) FROM tenant_custom_configs WHERE encrypted_value IS NOT NULL AND encrypted_value != ''
UNION ALL SELECT 'tenant_secrets', count(*) FROM tenant_secrets WHERE encrypted_secret IS NOT NULL AND encrypted_secret != ''
UNION ALL SELECT 'tool_builtin_providers', count(*) FROM tool_builtin_providers WHERE encrypted_credentials IS NOT NULL AND encrypted_credentials != ''
UNION ALL SELECT 'tool_api_providers', count(*) FROM tool_api_providers WHERE credentials_str IS NOT NULL AND credentials_str != ''
UNION ALL SELECT 'tool_mcp_providers', count(*) FROM tool_mcp_providers WHERE encrypted_credentials IS NOT NULL AND encrypted_credentials != ''
UNION ALL SELECT 'tool_oauth_tenant_clients', count(*) FROM tool_oauth_tenant_clients WHERE encrypted_oauth_params IS NOT NULL AND encrypted_oauth_params != ''
UNION ALL SELECT 'datasource', count(*) FROM datasource WHERE encrypted_credentials IS NOT NULL AND encrypted_credentials != ''
UNION ALL SELECT 'provider_models', count(*) FROM provider_models WHERE encrypted_config IS NOT NULL AND encrypted_config != ''
UNION ALL SELECT 'provider_tenants', count(*) FROM provider_tenants WHERE encrypted_config IS NOT NULL AND encrypted_config != '';
SQL

# 3. 检查 tenants 表中的 encrypt_public_key 是否与 minio 中私钥匹配（验证密钥对一致性）
docker-compose exec -T db_postgres psql -U postgres -d dify -c "SELECT id, encrypt_public_key FROM tenants WHERE id = '<TENANT_ID>';" 2>&1 | head -20

# 4. 查看 api 容器中实际调用的解密相关日志（用 --since 只看最近30分钟的）
docker-compose logs --since 30m api 2>&1 | grep -iE 'decrypt|encrypt|incorrect|rsa|private.*key|public.*key|cipher|bad' | tail -30
