#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-21 16:30
# Context: openai_api_compatible 修改凭据保存成功后，保存模型报 "the custom model record not found"。
#          判断：后端查 provider_models 无该 (model, model_type) 记录，但凭据记录存在——
#          疑似孤儿凭据（先删过模型，凭据残留）或凭据与保存模型请求的名称/类型不一致。
#          本轮核对两张表错位情况 + 抓 traceback 确认抛错函数。
# Cmds: 2 条 + 1 个浏览器取证项；在原 Compose 目录、原 shell 逐块粘贴执行（docker-compose 可能是函数）。全部只读。

# 0.（单行，可编辑）API 容器服务名，默认 api；不同就改等号后的值，再粘贴后面的块
DTR_API=api

# 1. 对比 provider_models 与 provider_model_credentials（openai_api_compatible 相关，含新旧两种 provider 名），
#    输出孤儿凭据 = "有凭据但没有对应模型记录"的组合
docker-compose exec -T "$DTR_API" python - <<'PY' 2>&1 | head -40
import logging
logging.disable(logging.CRITICAL)
from configs import dify_config
from sqlalchemy import create_engine, text

LIKE = '%openai_api_compatible%'
eng = create_engine(dify_config.SQLALCHEMY_DATABASE_URI, connect_args={'connect_timeout': 8})

def q(conn, sql):
    try:
        return conn.execute(text(sql), {'l': LIKE}).mappings().all()
    except Exception as e:
        print('QUERY_ERR', type(e).__name__, str(e)[:80])
        return []

with eng.connect() as conn:
    conn.execute(text('SET TRANSACTION READ ONLY'))
    conn.execute(text("SET LOCAL statement_timeout = '8s'"))
    ms = q(conn, "SELECT tenant_id, provider_name, model_name, model_type, is_valid"
                 " FROM provider_models WHERE provider_name LIKE :l ORDER BY model_type, model_name")
    cs = q(conn, "SELECT tenant_id, provider_name, credential_name, model_name, model_type"
                 " FROM provider_model_credentials WHERE provider_name LIKE :l ORDER BY model_type, model_name")
    print('MODELS_N=%d' % len(ms))
    for r in ms[:12]:
        print('M|t=%s|p=%s|m=%s|mt=%s|valid=%s' % (str(r['tenant_id'])[:8],
              r['provider_name'].split('/')[-1][:26], r['model_name'][:36], r['model_type'], r['is_valid']))
    print('CREDS_N=%d' % len(cs))
    for r in cs[:12]:
        print('C|t=%s|p=%s|m=%s|mt=%s|n=%s' % (str(r['tenant_id'])[:8],
              r['provider_name'].split('/')[-1][:26], r['model_name'][:36], r['model_type'],
              (r['credential_name'] or '')[:20]))
    mkeys = {(str(r['tenant_id']), r['model_name'], r['model_type']) for r in ms}
    orph = [r for r in cs if (str(r['tenant_id']), r['model_name'], r['model_type']) not in mkeys]
    print('ORPHAN_CRED_N=%d' % len(orph))
    for r in orph[:10]:
        print('O|t=%s|m=%s|mt=%s|n=%s' % (str(r['tenant_id'])[:8], r['model_name'][:36],
              r['model_type'], (r['credential_name'] or '')[:20]))
PY

# 2. 抓 api 最近日志里该报错的 traceback（含函数名与请求路径），确认是哪条代码路径抛的
docker-compose logs --tail=3000 "$DTR_API" 2>&1 | grep -iE -A12 "custom model record not found" | tail -32

# 3.（浏览器取证，非命令）F12 → Network → 复现一次"保存模型" → 找到 POST .../models 请求，回传：
#    请求 URL、请求体里的 model / model_type / credential_id(前8位即可) / config_from 字段、响应体。
#    不要回传 Authorization、Cookie 或 API Key 等凭据字段值。
