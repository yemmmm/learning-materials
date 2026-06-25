#!/usr/bin/env bash
# =============================================================================
# Changed: 2026-06-25 - 全面重构，移除监控服务检查
# 详细健康检查 - 验证关键链路
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "🔍 n8n HA 关键链路检查"
echo "========================"

fail=0
check() {
  local name="$1" cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "✅ $name"
  else
    echo "❌ $name"
    fail=$((fail + 1))
  fi
}

# 1. 容器运行状态
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
else
  COMPOSE="docker-compose"
fi

RUNNING=$($COMPOSE ps --status running -q 2>/dev/null | wc -l)
echo "   运行中容器: $RUNNING"

# 2. Redis 健康
REDIS_PASS=$(grep QUEUE_BULL_REDIS_PASSWORD .env 2>/dev/null | cut -d= -f2 || echo "")
check "Redis 健康" "docker exec n8n-redis redis-cli -a '$REDIS_PASS' --no-auth-warning ping 2>/dev/null | grep -q PONG"

# 3. n8n main 健康
check "n8n main 健康" "docker exec n8n-main wget -qO- http://localhost:5678/healthz 2>/dev/null"

# 4. n8n worker 健康
check "n8n worker 运行" "docker ps --filter name=n8n-worker --filter status=running -q | grep -q ."

# 5. Traefik 健康 + 路由
check "Traefik 健康" "curl -sf --max-time 3 http://localhost:8889/ping"
check "Traefik → n8n 路由" "curl -sf --max-time 3 http://localhost:80/healthz"

# 6. Task Runners
check "n8n-main-runner 运行" "docker ps --filter name=n8n-main-runner --filter status=running -q | grep -q ."
check "n8n-worker-runner 运行" "docker ps --filter name=n8n-worker-runner --filter status=running -q | grep -q ."

echo ""
if [[ $fail -eq 0 ]]; then
  echo "🎉 所有关键检查通过"
  exit 0
else
  echo "⚠️  有 $fail 项检查失败"
  exit 1
fi
