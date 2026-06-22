#!/usr/bin/env bash
# =============================================================================
# 初始化脚本 - 生成 .env、随机密码、加密密钥，准备数据目录权限
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

# 生成随机字符串
gen_str() {
  local len="${1:-32}"
  openssl rand -hex "$((len / 2))" 2>/dev/null || head -c "$len" /dev/urandom | base64 | tr -d '/+=' | head -c "$len"
}

gen_pass() {
  # 24 字符强密码，包含大小写字母数字
  head -c 32 /dev/urandom | base64 | tr -d '/+=' | head -c 24
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

N8N_KEY=$(gen_str 64)
PG_PASS=$(gen_pass)
REDIS_PASS=$(gen_pass)
MINIO_PASS=$(gen_pass)
GRAFANA_PASS=$(gen_pass)

sed -i \
  -e "s|CHANGE_ME_USE_openssl_rand_hex_32|$N8N_KEY|" \
  -e "s|CHANGE_ME_STRONG_PASSWORD|$PG_PASS|" \
  -e "s|CHANGE_ME_REDIS_PASSWORD|$REDIS_PASS|" \
  -e "s|CHANGE_ME_MINIO_STRONG_PASSWORD|$MINIO_PASS|" \
  -e "s|CHANGE_ME_GRAFANA_PASSWORD|$GRAFANA_PASS|" \
  "$ENV_FILE"

# 同步 Redis 密码到 redis.conf
sed -i "s|requirepass CHANGE_ME_REDIS_PASSWORD|requirepass $REDIS_PASS|" config/redis/redis.conf

echo "✅ .env 已生成"
echo ""
echo "🔐 关键凭据（请妥善保存）："
echo "   N8N_ENCRYPTION_KEY:    $N8N_KEY"
echo "   POSTGRES_PASSWORD:     $PG_PASS"
echo "   REDIS_PASSWORD:        $REDIS_PASS"
echo "   MINIO_ROOT_PASSWORD:   $MINIO_PASS"
echo "   GRAFANA_ADMIN_PASSWORD:$GRAFANA_PASS"
echo ""
echo "👉 下一步：./scripts/start.sh"
