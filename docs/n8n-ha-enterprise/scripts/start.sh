#!/usr/bin/env bash
# =============================================================================
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

echo "🚀 启动 n8n HA 集群..."
echo ""

# 创建数据目录（避免 docker 创建成 root 权限）
mkdir -p data/{postgres,redis,minio,grafana,prometheus} volumes/{n8n-main-1,n8n-main-2,n8n-worker-1,n8n-worker-2,n8n-worker-3}

# 拉镜像并启动
docker compose pull
docker compose up -d

echo ""
echo "⏳ 等待服务就绪（最多 120s）..."
for i in {1..24}; do
  if curl -sf http://localhost:5680/healthz >/dev/null 2>&1; then
    echo "✅ Traefik → n8n 已就绪"
    break
  fi
  sleep 5
  echo "   ...等待中（$((i*5))s）"
done

echo ""
echo "🌐 访问地址："
echo "   n8n UI:        http://localhost:5680"
echo "   Traefik Dash:  http://localhost:8889"
echo "   MinIO Console: http://localhost:9003"
echo "   Prometheus:    http://localhost:9090"
echo "   Grafana:       http://localhost:3001"
echo ""
echo "📊 容器状态："
docker compose ps
