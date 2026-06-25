#!/usr/bin/env bash
# =============================================================================
# Changed: 2026-06-25 - 全面重构，适配新的多服务器架构
# 初始化脚本 - 生成 .env、随机密码、加密密钥
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

# 生成随机字符串
gen_hex() {
  local len="${1:-32}"
  openssl rand -hex "$((len / 2))" 2>/dev/null || {
    cat /dev/urandom | tr -dc 'a-f0-9' | head -c "$len"
  }
}

gen_pass() {
  # 24 字符强密码
  cat /dev/urandom | tr -dc 'A-Za-z0-9' | head -c 24
}

if [[ -f "$ENV_FILE" ]]; then
  echo "⚠️  .env 已存在，跳过生成。如需重新生成，请先备份并删除 .env"
  exit 0
fi

if [[ ! -f "$EXAMPLE_FILE" ]]; then
  echo "❌ 找不到 $EXAMPLE_FILE"
  exit 1
fi

echo "📝 生成 .env ..."
cp "$EXAMPLE_FILE" "$ENV_FILE"

N8N_KEY=$(gen_hex 64)
RUNNER_TOKEN=$(gen_hex 64)
REDIS_PASS=$(gen_pass)
MINIO_PASS=$(gen_pass)

sed -i \
  -e "s|CHANGE_ME_USE_openssl_rand_hex_32|$N8N_KEY|" \
  -e "s|CHANGE_ME_RUNNER_AUTH_TOKEN|$RUNNER_TOKEN|" \
  -e "s|CHANGE_ME_REDIS_PASSWORD|$REDIS_PASS|" \
  -e "s|CHANGE_ME_MINIO_ROOT_PASSWORD|$MINIO_PASS|g" \
  "$ENV_FILE"

echo "✅ .env 已生成"
echo ""
echo "🔐 自动生成的凭据（请妥善保存）："
echo "   N8N_ENCRYPTION_KEY:  $N8N_KEY"
echo "   RUNNERS_AUTH_TOKEN:  $RUNNER_TOKEN"
echo "   REDIS_PASSWORD:      $REDIS_PASS"
echo "   MINIO_ROOT_PASSWORD: $MINIO_PASS"
echo ""
echo "⚠️  还需要手动配置以下外部 PostgreSQL 连接信息："
echo "   DB_POSTGRESDB_HOST"
echo "   DB_POSTGRESDB_DATABASE"
echo "   DB_POSTGRESDB_USER"
echo "   DB_POSTGRESDB_PASSWORD"
echo ""
echo "👉 配置完成后，运行 ./scripts/start.sh 启动服务"
echo ""
echo "📋 多服务器部署提醒："
echo "   副服务器 (10vm) 需要:"
echo "   1. 将 .env 和 docker-compose.worker.yml 复制到副服务器"
echo "   2. 副服务器 .env 中修改 QUEUE_BULL_REDIS_HOST=li19dksfai11vm.bmwgroup.net"
echo "   3. 确保 N8N_ENCRYPTION_KEY 和 RUNNERS_AUTH_TOKEN 与主服务器完全一致"
