#!/usr/bin/env bash
# =============================================================================
# Changed: 2026-06-25 - 全面重构，适配新架构
# 启动 n8n HA 集群
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 检查 .env
if [[ ! -f .env ]]; then
  echo "❌ 未找到 .env，请先运行 ./scripts/init.sh"
  exit 1
fi

# 检查 docker
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ 未找到 docker 命令"
  exit 1
fi

# 检查 compose 子命令
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "❌ 未找到 docker compose 或 docker-compose"
  exit 1
fi

echo "🚀 启动 n8n HA 集群（主服务器）..."
echo ""

# 创建数据目录
mkdir -p data/{redis,n8n-main,n8n-worker} config/traefik/{certs,logs}

# 拉镜像并启动
$COMPOSE pull
$COMPOSE up -d

echo ""
echo "⏳ 等待服务就绪..."
for i in {1..24}; do
  if curl -sf http://localhost:80/healthz >/dev/null 2>&1; then
    echo "✅ Traefik → n8n 已就绪"
    break
  fi
  sleep 5
  echo "   ...等待中 ($((i*5))s)"
done

echo ""
echo "🌐 访问地址："
echo "   n8n UI:        https://li19dksfai11vm.bmwgroup.net"
echo "   Traefik Dash:  http://localhost:8889  (仅本机)"
echo ""
echo "📊 容器状态："
$COMPOSE ps
