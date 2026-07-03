#!/usr/bin/env bash
# =============================================================================
# 启动 Prometheus + Grafana 监控扩展
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

if [[ ! -f .env ]]; then
  echo "❌ 未找到 .env，请先运行 ./scripts/init.sh"
  exit 1
fi

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
else
  echo "❌ 未找到 docker compose 命令"
  exit 1
fi

mkdir -p data/{prometheus,grafana}

echo "📈 启动监控服务..."
$COMPOSE --profile monitoring up -d prometheus grafana

echo ""
echo "🌐 访问地址："
echo "   Grafana:    http://localhost:${GRAFANA_PORT:-3001}"
echo "   Prometheus: http://localhost:${PROMETHEUS_PORT:-9090}  (默认仅本机绑定)"
echo ""
$COMPOSE --profile monitoring ps prometheus grafana
