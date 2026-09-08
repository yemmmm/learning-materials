#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08 08:13
# Context: 已用 0.1.0-0.1.2 复现 3.10->3.11 新增 RBAC 未继承旧服务自定义 DIFY_DB_NAME；真实 Compose 复核成立。生产原因待证，检查企业 DB 别名及 envs 文件升级遗漏。
# Cmds: 2 条
# 两套环境各在 Compose 目录，把每条命令完整粘贴到平时 docker-compose 可用的终端。无需 source。
# 不修改数据库、容器或配置；变量缺失仅报告，不能直接认定应用没有默认值。

# 1. 实际容器中的数据库别名、迁移/同步配置、跨服务凭据一致性（最多 28 行；凭据只报状态/是否相等）
docker inspect $(docker-compose ps -q api worker dify-enterprise dify-enterprise-rbac) | python3 -c '
import json,sys
from urllib.parse import urlsplit
try: objects=json.load(sys.stdin)
except ValueError: print("INSPECT_FAILED"); raise SystemExit(0)
envs={}
def state(e,k): return "UNSET" if k not in e else "EMPTY" if not e[k] else "SET"
def show(e,k):
    if k not in e: return "<unset>"
    if not e[k]: return "<empty>"
    if "URL" in k:
        try:
            u=urlsplit(e[k]); return (u.scheme+"://"+str(u.hostname)+(":"+str(u.port) if u.port else "")+u.path) if u.hostname else "<invalid-url>"
        except ValueError: return "<invalid-url>"
    return e[k]
for o in objects[:4]:
    svc=(o["Config"].get("Labels") or {}).get("com.docker.compose.service",o["Name"])
    e=dict(x.split("=",1) for x in o["Config"].get("Env",[]) if "=" in x); envs[svc]=e
    print("SERVICE",svc,o["Config"]["Image"])
    print("DB", " ".join(k+"="+show(e,k) for k in ["DB_HOST","DB_PORT","DB_DATABASE","DIFY_DB_NAME","ENTERPRISE_DB_NAME","DB_ENGINE","DB_SSL_MODE"]))
    print("FLOW"," ".join(k+"="+show(e,k) for k in ["RBAC_ENABLED","ENTERPRISE_RBAC_API_URL","ENTERPRISE_RBAC_REQUEST_TIMEOUT","RBAC_INNER_BASE_URL","MIGRATION_ENABLED","WORKSPACE_SYNC_CRON","WORKSPACE_SYNC_TIMEOUT"]))
    print("CREDENTIAL_STATE"," ".join(k+"="+state(e,k) for k in ["DB_USER","DB_PASS","DIFY_DB_USER","DIFY_DB_PASS","ENTERPRISE_DB_USER","ENTERPRISE_DB_PASS","ENTERPRISE_API_SECRET_KEY"]))
def compare(label,left,lk,right,rk):
    a,b=envs.get(left,{}),envs.get(right,{})
    result="MISSING_OR_EMPTY" if not a.get(lk) or not b.get(rk) else "EQUAL" if a[lk]==b[rk] else "DIFFERENT"
    print("COMPARE",label,result)
for svc in ["dify-enterprise","dify-enterprise-rbac"]:
    compare(svc+".core_database","api","DB_DATABASE",svc,"DIFY_DB_NAME")
    compare(svc+".inner_secret","api","ENTERPRISE_API_SECRET_KEY",svc,"ENTERPRISE_API_SECRET_KEY")
for k in ["DIFY_DB_NAME","ENTERPRISE_DB_NAME","DB_USER","DB_PASS","DIFY_DB_USER","DIFY_DB_PASS","ENTERPRISE_DB_USER","ENTERPRISE_DB_PASS"]:
    compare("enterprise_vs_rbac."+k,"dify-enterprise",k,"dify-enterprise-rbac",k)
'

# 2. envs 文件是否缺失/仍为旧版，以及根 .env 是否有关键覆盖（最多 18 行；不输出密码或自定义文件哈希）
python3 - <<'PY'
import pathlib,hashlib,re
catalog={
"envs/enterprise/core.env": {"hashes":{"cffa57bd2cd3b24ad8dde0f326e12c38943dd500fd731758bccbdf0f3531d4fa":["3.10.0","3.11.0","3.12.0","3.12.1"]},"keys":["ENTERPRISE_DOMAIN","ENTERPRISE_URL","INNER_API_KEY","ENTERPRISE_API_SECRET_KEY","DASHBOARD_JWT_SECRET_KEY"]},
"envs/enterprise/db.env": {"hashes":{"66527b819e97b89613295d11ea87c941b833d0b236c3ece5a1e7864ea13d7882":["3.10.0","3.11.0","3.12.0","3.12.1"]},"keys":["DB_ENGINE","DB_USER","DB_PASS","DB_TZ","DB_SSL_MODE","DB_URI_SCHEME","DB_EXTRAS","DB_PARAMS","DB_TLS","DIFY_DB_NAME","ENTERPRISE_DB_NAME","AUDIT_DB_NAME","PLUGIN_DB_NAME","DIFY_DB_USER","DIFY_DB_PASS","ENTERPRISE_DB_USER","ENTERPRISE_DB_PASS","AUDIT_DB_USER","AUDIT_DB_PASS","PLUGIN_DB_USER","PLUGIN_DB_PASS"]},
"envs/enterprise/shared.env": {"hashes":{"ae7b372b7571fcc3c0742c465c5a92455da47e79fc44da26d106fb65508520b9":["3.10.0"],"d0f6678362e1e9c0185702f0d19a0953eb1e27cb5661c90944e9bc32b3bdad25":["3.11.0"],"7fa269a38b0637800213eb91e6f5b3cd35f4be921b686d75c0392b9009235caf":["3.12.0"],"931f30ed65780badbfe2c349a522276ef4cb47458e1040e64841a77f10a1662f":["3.12.1"]},"keys":["INNER_API","INNER_API_KEY","ENTERPRISE_API_SECRET_KEY","ENTERPRISE_ENABLED","ENTERPRISE_API_URL","ENTERPRISE_PLUGIN_MANAGER_API_SECRET_KEY","ENTERPRISE_PLUGIN_MANAGER_API_URL","MODEL_LB_ENABLED","RBAC_ENABLED","ENTERPRISE_RBAC_API_URL","ENTERPRISE_RBAC_REQUEST_TIMEOUT","WEBAPP_PUBLIC_ACCESS_ENABLED","ENABLE_LICENSE_EXPIRY_NOTICE","DB_EXTRAS","DB_SSL_MODE","SQLALCHEMY_DATABASE_URI_SCHEME","DB_CHARSET","LOG_OUTPUT_FORMAT","OTLP_API_KEY","CELERY_QUEUES","PLUGIN_MODEL_PROVIDERS_CACHE_ENABLED","ENTERPRISE_TELEMETRY_ENABLED","ENTERPRISE_OTLP_ENDPOINT","ENTERPRISE_OTLP_PROTOCOL","ENTERPRISE_OTLP_HEADERS","ENTERPRISE_INCLUDE_CONTENT","ENTERPRISE_SERVICE_NAME","ENTERPRISE_OTEL_SAMPLING_RATE"]},
"envs/enterprise/enterprise.env": {"hashes":{"3a804cb87d1f13d4b505e04534638754e4d51542bb458d409c2780953a8dd4f3":["3.10.0"],"0f501adffca741cf8cef8102ad5aab0bd5d2dd11e4532ff2e87b275471067700":["3.11.0","3.12.0","3.12.1"]},"keys":["ENTERPRISE_SECRET_KEY_SALT","DIFY_ENDPOINT","MIGRATION_ENABLED","CONSOLE_SSO_SKIP_CERT_VERIFY","WEB_SSO_SKIP_CERT_VERIFY","SERVER_TIMEOUT","PLUGIN_MANAGER_HTTP_ADDR","PLUGIN_MANAGER_GRPC_ADDR","PLUGIN_MANAGER_CLIENT_TIMEOUT","RBAC_INNER_BASE_URL","WORKSPACE_SYNC_CRON","WORKSPACE_SYNC_TIMEOUT","MQ_SHARD_COUNT","EVENT_BUS_STREAMS_RETENTION_SECONDS","DEPLOY_ENV","DB_SLOW_QUERY_THRESHOLD","ENABLE_OTEL","OTEL_SAMPLING_RATE","ENTERPRISE_OTLP_ENDPOINT","ENTERPRISE_OTLP_PROTOCOL","ENTERPRISE_OTLP_HEADERS","ENTERPRISE_INCLUDE_CONTENT","ENTERPRISE_SERVICE_NAME","OTLP_TRACE_ENDPOINT","OTLP_METRIC_ENDPOINT","OTLP_BASE_ENDPOINT","OTLP_API_KEY","OTEL_EXPORTER_OTLP_PROTOCOL","OTEL_EXPORTER_TYPE","OTEL_BATCH_EXPORT_SCHEDULE_DELAY","OTEL_MAX_QUEUE_SIZE","OTEL_MAX_EXPORT_BATCH_SIZE","OTEL_METRIC_EXPORT_INTERVAL","OTEL_BATCH_EXPORT_TIMEOUT","OTEL_METRIC_EXPORT_TIMEOUT","ENTERPRISE_GO_OTEL_SDK_DISABLED","ENTERPRISE_GO_OTEL_EXPORTER_OTLP_ENDPOINT","ENTERPRISE_GO_OTEL_EXPORTER_OTLP_PROTOCOL","ENTERPRISE_GO_OTEL_EXPORTER_OTLP_HEADERS","ENTERPRISE_GO_OTEL_TRACES_EXPORTER","ENTERPRISE_GO_OTEL_METRICS_EXPORTER","ENTERPRISE_GO_OTEL_TRACES_SAMPLER","ENTERPRISE_GO_OTEL_TRACES_SAMPLER_ARG","ENTERPRISE_GO_OTEL_RESOURCE_ATTRIBUTES"]},
"envs/enterprise/rbac.env": {"hashes":{"be1184d0fc9e36fb981bd82ae15b3a9053bcf279699888ef742a5a9e36143a44":["3.11.0","3.12.0","3.12.1"]},"keys":["SERVER_TIMEOUT","GRPC_SERVER_TIMEOUT"]},
"envs/enterprise/redis.env": {"hashes":{"3af4d3c27d7e46efdd80f721c6755a261c41dbd9e235dadc3e6d648e13531e95":["3.10.0","3.11.0","3.12.0","3.12.1"]},"keys":["REDIS_MODE","REDIS_SENTINEL_ADDRS","REDIS_READ_TIMEOUT","REDIS_WRITE_TIMEOUT","REDIS_DIAL_TIMEOUT","REDIS_MAX_RETRIES"]}
}
def assignments(text):
    result={}
    for line in text.splitlines():
        m=re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$",line)
        if m: result.setdefault(m.group(1),[]).append(m.group(2).strip())
    return result
for rel,meta in catalog.items():
    p=pathlib.Path(rel)
    if not p.is_file():
        print("FILE",rel,"MISSING"); continue
    raw=p.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    values=assignments(raw.decode("utf-8",errors="replace"))
    missing=[k for k in meta["keys"] if k not in values]
    print("FILE",rel,"official_versions="+",".join(meta["hashes"].get(digest,["custom_or_other_version"])),
          "absent_keys="+str(missing[:12]),"absent_count="+str(len(missing)))
root=pathlib.Path(".env")
if not root.is_file(): print("ROOT_ENV MISSING")
else:
    values=assignments(root.read_text())
    for keys in [
        ["DB_DATABASE","DIFY_DB_NAME","ENTERPRISE_DB_NAME","DB_USER","DB_PASS","DIFY_DB_USER","DIFY_DB_PASS","ENTERPRISE_DB_USER","ENTERPRISE_DB_PASS"],
        ["RBAC_ENABLED","ENTERPRISE_RBAC_API_URL","RBAC_INNER_BASE_URL","ENTERPRISE_API_SECRET_KEY"],
        ["MIGRATION_ENABLED","WORKSPACE_SYNC_CRON","WORKSPACE_SYNC_TIMEOUT","ENTERPRISE_RBAC_REQUEST_TIMEOUT"]]:
        print("ROOT_DECLARATIONS"," ".join(k+":"+("ABSENT" if k not in values else "EMPTY" if values[k][-1] in ["","\"\"","''"] else "PRESENT")+(":DUPLICATE" if len(values.get(k,[]))>1 else "") for k in keys))
print("File mismatch/absence alone is NOT a fault: equivalent values may be in compose environment or another env_file. Command 1 is the runtime evidence.")
PY
