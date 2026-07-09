#!/usr/bin/env python3
"""Dify privkey 恢复工具 —— 生成新 RSA 密钥对，写入 storage，输出公钥。

Usage:
    python regen_privkey.py <tenant_id>

输出 ===NEW PUBKEY BEGIN=== 到 ===NEW PUBKEY END=== 之间的公钥，
用于后续 UPDATE tenants.encrypt_public_key。
"""

import sys

if len(sys.argv) != 2:
    print("Usage: python regen_privkey.py <tenant_id>", file=sys.stderr)
    sys.exit(1)

tenant_id = sys.argv[1]

from app import app

with app.app_context():
    from extensions.ext_storage import storage
    from Crypto.PublicKey import RSA

    key = RSA.generate(2048)
    priv = key.export_key()
    pub = key.publickey().export_key().decode()

    filepath = f"privkeys/{tenant_id}/private.pem"
    storage.save(filepath, priv)

    print("===NEW PUBKEY BEGIN===")
    print(pub)
    print("===NEW PUBKEY END===")
