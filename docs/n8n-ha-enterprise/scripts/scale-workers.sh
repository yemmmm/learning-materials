#!/usr/bin/env bash
# =============================================================================
# Changed: 2026-06-25 - 全面重构，适配新架构
# 扩缩容 n8n worker
#
# 用法:
#   主服务器:  ./scripts/scale-workers.sh 3
#   副服务器:  在 docker-compose.worker.yml 目录下:
#             docker compose -f docker-compose.worker.yml up -d --scale n8n-worker=3
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

TARGET="${1:-1}"
if [[ "$TARGET" -lt 1 || "$TARGET" -gt 20 ]]; then
  echo "❌ 目标 worker 数应在 1-20 之间"
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
else
  COMPOSE="docker-compose"
fi

echo "🔢 调整 worker 数量为 $TARGET ..."
echo ""

# 检查当前由哪个 compose 文件管理
if [[ -f "docker-compose.yml" ]]; then
  COMPOSE_FILE="docker-compose.yml"
elif [[ -f "docker-compose.worker.yml" ]]; then
  COMPOSE_FILE="docker-compose.worker.yml"
else
  echo "❌ 未找到 compose 文件"
  exit 1
fi

echo "⚠️  注意: 由于 worker 配有 task_runner sidecar，"
echo "   docker compose --scale 不会自动扩 runner。"
echo ""
echo "   推荐做法："
echo "   1. 在 compose 文件中手动复制 n8n-worker / n8n-worker-runner 服务定义"
echo "   2. 或接受多个 worker 共用同一个 runner（Code 节点可能有排队）"
echo ""
echo "   当前使用 scale 方式启动（仅 worker 扩容，runner 不变）:"
$COMPOSE -f "$COMPOSE_FILE" up -d --scale n8n-worker="$TARGET"

echo ""
echo "📊 容器状态："
$COMPOSE -f "$COMPOSE_FILE" ps
