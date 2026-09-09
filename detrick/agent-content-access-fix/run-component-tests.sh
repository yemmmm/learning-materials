#!/usr/bin/env sh
set -eu

# Run the focused boundary suite against a real PostgreSQL container and the
# supplied API image. Only the external RBAC response is stubbed by pytest.

API_IMAGE=${1:?usage: $0 API_IMAGE PREPARED_OUTPUT_DIR}
PREPARED_DIR=${2:?usage: $0 API_IMAGE PREPARED_OUTPUT_DIR}
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

case "$PREPARED_DIR" in
  /*) ;;
  *) printf '%s\n' "PREPARED_DIR must be an absolute path: $PREPARED_DIR" >&2; exit 2 ;;
esac
test -r "$PREPARED_DIR/wraps.patched.py"

expected_patched_sha256=$(awk -F= '$1 == "patched_sha256" {print $2}' "$PREPARED_DIR/manifest.txt")
actual_patched_sha256=$(sha256sum "$PREPARED_DIR/wraps.patched.py" | awk '{print $1}')
if [ "$actual_patched_sha256" != "$expected_patched_sha256" ]; then
  printf '%s\n' "prepared module hash does not match manifest" >&2
  exit 3
fi

run_id=${AGENT_FIX_TEST_ID:-$$}
network_name="agent-content-test-network-$run_id"
postgres_name="agent-content-test-postgres-$run_id"
postgres_user=agent_fix_test
postgres_db=agent_fix_test
postgres_password="agent_fix_$run_id"
database_url="postgresql+psycopg2://$postgres_user:$postgres_password@agent-content-test-postgres-$run_id:5432/$postgres_db"

cleanup() {
  docker rm -f "$postgres_name" >/dev/null 2>&1 || true
  docker network rm "$network_name" >/dev/null 2>&1 || true
}
trap cleanup EXIT HUP INT TERM

docker network create --internal "$network_name" >/dev/null
docker run -d --name "$postgres_name" --network "$network_name" \
  -e POSTGRES_USER="$postgres_user" \
  -e POSTGRES_PASSWORD="$postgres_password" \
  -e POSTGRES_DB="$postgres_db" \
  postgres:15-alpine >/dev/null

ready=0
attempt=0
while [ "$attempt" -lt 30 ]; do
  if docker exec "$postgres_name" pg_isready -U "$postgres_user" -d "$postgres_db" >/dev/null 2>&1; then
    ready=1
    break
  fi
  attempt=$((attempt + 1))
  sleep 1
done
if [ "$ready" -ne 1 ]; then
  printf '%s\n' "temporary PostgreSQL did not become ready" >&2
  exit 4
fi

docker run --rm --network "$network_name" --entrypoint python \
  -e AGENT_FIX_TEST_DATABASE_URL="$database_url" \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$SCRIPT_DIR/tests/test_agent_content_access_fix.py:/tmp/test_agent_content_access_fix.py:ro" \
  -v "$PREPARED_DIR/wraps.patched.py:/app/api/controllers/common/wraps.py:ro" \
  "$API_IMAGE" -m pytest -q -p no:cacheprovider /tmp/test_agent_content_access_fix.py

printf '%s\n' "component_tests=PASS"
printf '%s\n' "database=temporary PostgreSQL 15 container"
printf '%s\n' "patched_sha256=$actual_patched_sha256"
