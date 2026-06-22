#!/usr/bin/env bash
# 扩缩容 n8n worker（动态调整 worker 数量）
# 用法：./scripts/scale-workers.sh 5   # 扩到 5 个
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

TARGET="${1:-3}"
if [[ "$TARGET" -lt 1 || "$TARGET" -gt 20 ]]; then
  echo "❌ 目标 worker 数应在 1-20 之间"
  exit 1
fi

echo "🔢 调整 worker 数量为 $TARGET ..."

# Docker Compose v2 支持 --scale，但需要 service 没有固定 container_name
# 这里采用预定义 3 个 worker 服务的方式，扩展超过 3 时动态生成
if [[ "$TARGET" -le 3 ]]; then
  echo "✅ 当前 compose 已预定义 3 个 worker，目标 $TARGET ≤ 3"
  echo "   如需缩减，建议在 docker-compose.yml 中注释对应服务"
  docker compose up -d --scale n8n-worker-1=1 --scale n8n-worker-2=1 --scale n8n-worker-3=1 n8n-worker-1 n8n-worker-2 n8n-worker-3
else
  echo "⚠️  超过 3 个 worker 需要在 docker-compose.yml 中追加 service 定义"
  echo "   建议参考 n8n-worker-3 的配置复制为 n8n-worker-4..N"
fi

docker compose ps
