#!/usr/bin/env bash
# =============================================================================
# Changed: 2026-06-25 - 全面重构，适配新架构
# 扩缩容 n8n worker
#
# 用法:
#   主服务器:  ./scripts/scale-workers.sh 2
#   副服务器:  docker-compose -f docker-compose.worker.yml up -d n8n-worker-1 n8n-worker-1-runner
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

TARGET="${1:-1}"
if [[ "$TARGET" -lt 1 || "$TARGET" -gt 2 ]]; then
  echo "❌ 当前 compose 显式定义了 2 组 worker/runner，目标 worker 数应在 1-2 之间"
  echo "   如需更多，请复制 n8n-worker-N 与 n8n-worker-N-runner 成对服务定义。"
  exit 1
fi

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "❌ 未找到 docker-compose 命令"
  exit 1
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

if [[ "$TARGET" -eq 1 ]]; then
  $COMPOSE -f "$COMPOSE_FILE" up -d n8n-worker-1 n8n-worker-1-runner
  $COMPOSE -f "$COMPOSE_FILE" stop n8n-worker-2 n8n-worker-2-runner >/dev/null 2>&1 || true
else
  $COMPOSE -f "$COMPOSE_FILE" up -d \
    n8n-worker-1 n8n-worker-1-runner \
    n8n-worker-2 n8n-worker-2-runner
fi

echo ""
echo "📊 容器状态："
$COMPOSE -f "$COMPOSE_FILE" ps
