#!/usr/bin/env bash
# 查看 n8n HA 集群状态
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "🐳 容器状态："
docker compose ps
echo ""

echo "🏥 健康检查："
declare -A SERVICES=(
  ["Traefik"]="http://localhost:8889/ping"
  ["n8n (via LB)"]="http://localhost:5680/healthz"
  ["Postgres"]="localhost:5434"
  ["MinIO"]="http://localhost:9002/minio/health/live"
  ["Prometheus"]="http://localhost:9090/-/healthy"
  ["Grafana"]="http://localhost:3001/api/health"
)

for name in "${!SERVICES[@]}"; do
  url="${SERVICES[$name]}"
  if [[ "$url" == http://* ]]; then
    if curl -sf --max-time 3 "$url" >/dev/null 2>&1; then
      echo "   ✅ $name"
    else
      echo "   ❌ $name ($url)"
    fi
  fi
done

echo ""
echo "📈 Redis 队列状态："
REDIS_PASS=$(grep REDIS_PASSWORD .env | cut -d= -f2)
docker exec n8n-ha-redis redis-cli -a "$REDIS_PASS" --no-auth-warning LLEN bull:jobs 2>/dev/null | awk '{print "   队列任务数:", $1}' || echo "   (无法获取)"

echo ""
echo "🐘 PostgreSQL 连接数："
docker exec n8n-ha-postgres psql -U "$(grep POSTGRES_USER .env | cut -d= -f2)" -d "$(grep POSTGRES_DB .env | cut -d= -f2)" -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | awk '{print "   活跃连接:", $1}' || echo "   (无法获取)"
