#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-09 14:50
# Context: 用户选路径 B 执行修复：① api 容器内调 Dify storage 模块生成 2048 位新 RSA 密钥对，privkey 写入 minio 覆盖 AI 假密钥 ② 打印新公钥 ③ 清 redis 的 privkey 缓存 ④ 把新公钥 UPDATE 到 tenants.encrypt_public_key + 清空 tool_*_providers 所有加密字段 ⑤ 重启 api/worker。完成后到控制台"工具"页重配每个工具的凭证
# Cmds: 4 条（必须按 1→2→3→4 顺序执行，命令 3 执行前手动把命令 1 输出的公钥粘到 SQL 占位符里）
# 替换占位符：<TENANT_ID> = privkeys/<TENANT_ID>/private.pem 里的目录名；<PASTE_NEW_PUBKEY> = 命令 1 打印的整段公钥（含 BEGIN/END PUBLIC KEY 两个头尾标记行）

# 1. api 容器内通过 Dify 的 app context 加载 storage 模块，生成新 RSA 2048 密钥对：privkey 写入 minio 覆盖现有文件（AI 生成的假密钥作废），公钥打印到屏幕。复制 ===NEW PUBKEY BEGIN=== 到 ===NEW PUBKEY END=== 之间的整段（含 ----- BEGIN/END PUBLIC KEY -----）
docker-compose exec -T api python -c "
from app import app
with app.app_context():
    from extensions.ext_storage import storage
    from Crypto.PublicKey import RSA
    key = RSA.generate(2048)
    priv = key.export_key()
    pub = key.publickey().export_key().decode()
    storage.save('privkeys/<TENANT_ID>/private.pem', priv)
    print('===NEW PUBKEY BEGIN===')
    print(pub)
    print('===NEW PUBKEY END===')
" 2>&1 | grep -A 30 'NEW PUBKEY BEGIN' | head -30

# 2. 清 redis 里 privkey 缓存（rsa.py 第 56 行 setex 120s 缓存私钥，不清的话 api 进程还用着旧私钥）
docker-compose exec -T redis sh -c "redis-cli --scan --pattern 'tenant_privkey:*' | xargs -r redis-cli DEL" 2>&1 | tail -5

# 3. 用新公钥 UPDATE tenants.encrypt_public_key（让加密/解密用同一对密钥），同时清空 tool_*_providers 所有加密字段（先手动编辑本条命令，把 <TENANT_ID> 和 <PASTE_NEW_PUBKEY> 替换好；公钥含换行没问题，psql heredoc 支持）
docker-compose exec -T db_postgres psql -U postgres -d dify 2>&1 <<SQL | tail -30
UPDATE tenants SET encrypt_public_key = '<PASTE_NEW_PUBKEY>' WHERE id = '<TENANT_ID>';
UPDATE tool_builtin_providers SET encrypted_credentials = '' WHERE tenant_id = '<TENANT_ID>';
UPDATE tool_api_providers SET credentials_str = '' WHERE tenant_id = '<TENANT_ID>';
UPDATE tool_mcp_providers SET encrypted_credentials = '', encrypted_headers = '' WHERE tenant_id = '<TENANT_ID>';
UPDATE tool_oauth_tenant_clients SET encrypted_oauth_params = '' WHERE tenant_id = '<TENANT_ID>';
SQL

# 4. 重启 api 和 worker，让进程内任何 RSA key 缓存失效（命令 2 清的是 redis，命令 4 清的是进程内存）
docker-compose restart api worker 2>&1 | tail -10
