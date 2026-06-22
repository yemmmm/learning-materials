#!/usr/bin/env bash
# 停止 n8n HA 集群
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "🛑 停止 n8n HA 集群..."
docker compose stop
echo "✅ 已停止（数据保留）"
echo ""
echo "💡 如需完全清理（含数据卷），运行："
echo "   docker compose down -v   # ⚠️  会删除所有数据"
