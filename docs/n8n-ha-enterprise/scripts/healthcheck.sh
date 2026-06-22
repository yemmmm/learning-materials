#!/usr/bin/env bash
# 详细健康检查 - 验证 HA 关键链路
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

# 1. 所有容器运行
RUNNING=$(docker compose ps --status running -q | wc -l)
TOTAL=$(docker compose config --services | wc -l)
if [[ "$RUNNING" -ge "$((TOTAL - 1))" ]]; then   # -1 容错 minio-init 一次性任务
  echo "✅ 容器运行：$RUNNING/$TOTAL"
else
  echo "❌ 容器运行：$RUNNING/$TOTAL"
  fail=$((fail + 1))
fi

# 2. PostgreSQL 健康
check "PostgreSQL 健康" "docker exec n8n-ha-postgres pg_isready -U n8n"

# 3. Redis 健康
REDIS_PASS=$(grep REDIS_PASSWORD .env | cut -d= -f2)
check "Redis 健康" "docker exec n8n-ha-redis redis-cli -a $REDIS_PASS --no-auth-warning ping"

# 4. MinIO 健康
check "MinIO 健康" "curl -sf http://localhost:9002/minio/health/live"

# 5. n8n main 实例健康（直连）
check "n8n-main-1 健康" "docker exec n8n-ha-main-1 wget -qO- http://localhost:5678/healthz"
check "n8n-main-2 健康" "docker exec n8n-ha-main-2 wget -qO- http://localhost:5678/healthz"

# 6. Traefik LB 健康且能转发
check "Traefik 健康" "curl -sf http://localhost:8889/ping"
check "Traefik → n8n 路由" "curl -sf http://localhost:5680/healthz"

# 7. Worker 节点运行
for w in worker-1 worker-2 worker-3; do
  check "n8n-$w 运行" "docker ps --filter name=n8n-ha-$w --filter status=running -q | grep -q ."
done

# 8. Prometheus 抓取目标
check "Prometheus 健康" "curl -sf http://localhost:9090/-/healthy"
echo ""
echo "  Prometheus 抓取目标状态："
curl -sf http://localhost:9090/api/v1/targets 2>/dev/null | \
  python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for t in data.get('data', {}).get('activeTargets', []):
        status = '✅' if t['health'] == 'up' else '❌'
        print(f\"    {status} {t['labels'].get('job', '?')}: {t['scrapeUrl']}\")
except: print('    (无法解析)')
" 2>/dev/null || echo "    (无法获取)"

echo ""
if [[ $fail -eq 0 ]]; then
  echo "🎉 所有关键检查通过"
  exit 0
else
  echo "⚠️  有 $fail 项检查失败"
  exit 1
fi
