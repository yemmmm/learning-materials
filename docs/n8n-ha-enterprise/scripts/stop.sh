#!/usr/bin/env bash
# 停止 n8n HA 集群
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 检测 compose 命令
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "❌ 未找到 docker compose 或 docker-compose"
  exit 1
fi

echo "🛑 停止 n8n HA 集群..."
$COMPOSE stop
echo "✅ 已停止（数据保留在 ./data 目录）"
echo ""
echo "💡 如需完全清理（含数据卷），运行："
echo "   $COMPOSE down -v   # ⚠️ 会删除所有数据"
