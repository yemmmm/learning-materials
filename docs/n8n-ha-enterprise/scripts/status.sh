#!/usr/bin/env bash
# =============================================================================
# Changed: 2026-06-25 - 全面重构，移除监控服务检查
# 查看 n8n HA 集群状态
# =============================================================================
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

echo "🐳 容器状态："
$COMPOSE ps
echo ""

echo "🏥 健康检查："
# Traefik
if curl -sf --max-time 3 http://localhost:8889/ping >/dev/null 2>&1; then
  echo "   ✅ Traefik"
else
  echo "   ❌ Traefik"
fi

# n8n (via LB)
if curl -sf --max-time 3 http://localhost:80/healthz >/dev/null 2>&1; then
  echo "   ✅ n8n (via Traefik)"
else
  echo "   ❌ n8n (via Traefik)"
fi

# Redis
if [[ -f .env ]]; then
  REDIS_PASS=$(grep QUEUE_BULL_REDIS_PASSWORD .env 2>/dev/null | cut -d= -f2 || echo "")
  if [[ -n "$REDIS_PASS" ]]; then
    if docker exec n8n-redis redis-cli -a "$REDIS_PASS" --no-auth-warning ping 2>/dev/null | grep -q PONG; then
      echo "   ✅ Redis"
    else
      echo "   ❌ Redis"
    fi
  fi
fi

echo ""
echo "📈 队列状态："
if [[ -n "${REDIS_PASS:-}" ]]; then
  docker exec n8n-redis redis-cli -a "$REDIS_PASS" --no-auth-warning LLEN bull:jobs 2>/dev/null | \
    awk '{print "   队列待处理任务数:", $1}' || echo "   (无法获取)"
fi
