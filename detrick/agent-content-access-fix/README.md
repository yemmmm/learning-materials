# Workspace Agent content access fix

This package implements the scoped rule from `requirement.md`: a member with
the current workspace `agent.manage` permission may view, edit, and debug all
active app-backed roster Agents in that workspace. The decision is evaluated
on each Console App authorization request; no Agent whitelist rows are added.

The production change is one version-checked patch to
`/app/api/controllers/common/wraps.py`. It is limited to the Flask `console`
blueprint and the `APP_VIEW_LAYOUT`, `APP_EDIT`, and `APP_TEST_AND_RUN` scenes.
OpenAPI, ordinary Apps, workflow-only Agents, published channels, API keys,
delete/publish controls, and existing legacy guards retain their current paths.

## Prepare on the closed host

Copy this directory to the deployment directory on the host and run these
commands in the existing shell. The image is read from the running API
container; no registry name or credential is guessed.

```sh
export DEPLOYMENT_PWD='/absolute/path/to/the/loaded-compose-directory'
cd "$DEPLOYMENT_PWD"
API_CID=$(docker-compose ps -q api)
WS_CID=$(docker-compose ps -q api_websocket)
API_IMAGE_ID=$(docker inspect --format '{{.Image}}' "$API_CID")
WS_IMAGE_ID=$(docker inspect --format '{{.Image}}' "$WS_CID")
test "$API_IMAGE_ID" = "$WS_IMAGE_ID"
AGENT_FIX_SOURCE_SHA256=a55bde316d9550353d2f2b4f3c9aa83f9085cbe34cc1f01767d50c6b11c11d9c
test "$(docker run --rm --network none --entrypoint cat "$API_IMAGE_ID" /app/api/controllers/common/wraps.py | sha256sum | awk '{print $1}')" = "$AGENT_FIX_SOURCE_SHA256"
export AGENT_FIX_OUTPUT_DIR="$DEPLOYMENT_PWD/agent-content-access-fix-applied"
./prepare-agent-content-fix.sh "$API_IMAGE_ID" "$AGENT_FIX_OUTPUT_DIR"
cat "$AGENT_FIX_OUTPUT_DIR/manifest.txt"
```

Preparation reads the module from the exact running image, checks the expected
SHA-256, and stops before producing a patched module when the bytes differ. It
then compiles the patched source with the image's Python 3.12 interpreter.
Preparation does not start a service and does not connect to the Dify database.

Expected source hash for the reviewed baseline:

```text
a55bde316d9550353d2f2b4f3c9aa83f9085cbe34cc1f01767d50c6b11c11d9c
```

If the hash check fails, stop and regenerate the patch against that exact
image. Do not overwrite the module by hand.

## Install through the existing Compose function

Record the current source hash from both serving containers before changing the
loaded Compose file. An unknown current hash is a stop condition.

```sh
API_CID=$(docker-compose ps -q api)
WS_CID=$(docker-compose ps -q api_websocket)
AGENT_FIX_SOURCE_SHA256=a55bde316d9550353d2f2b4f3c9aa83f9085cbe34cc1f01767d50c6b11c11d9c
test "$(docker exec "$API_CID" sha256sum /app/api/controllers/common/wraps.py | awk '{print $1}')" = "$AGENT_FIX_SOURCE_SHA256"
test "$(docker exec "$WS_CID" sha256sum /app/api/controllers/common/wraps.py | awk '{print $1}')" = "$AGENT_FIX_SOURCE_SHA256"
```

Save a copy of the Compose file that the existing `docker-compose` shell
function loads. In the already-loaded `api.volumes` and
`api_websocket.volumes` blocks, keep every existing entry and add exactly one
read-only entry to each:

```yaml
services:
  api:
    volumes:
      - "${AGENT_FIX_OUTPUT_DIR}/wraps.patched.py:/app/api/controllers/common/wraps.py:ro"
  api_websocket:
    volumes:
      - "${AGENT_FIX_OUTPUT_DIR}/wraps.patched.py:/app/api/controllers/common/wraps.py:ro"
```

Run the existing function from the same deployment directory. Do not construct
a new Compose command with guessed files or profiles, and do not recreate
workers, beat, collector, databases, networks, or volumes:

```sh
docker-compose up -d --no-deps --force-recreate api api_websocket
```

The effective mount is the persistent host file
`$AGENT_FIX_OUTPUT_DIR/wraps.patched.py` at
`/app/api/controllers/common/wraps.py` in both services. Verify the source
hash, a fresh Python import, and service state:

```sh
API_CID=$(docker-compose ps -q api)
WS_CID=$(docker-compose ps -q api_websocket)
docker exec "$API_CID" sha256sum /app/api/controllers/common/wraps.py
docker exec "$WS_CID" sha256sum /app/api/controllers/common/wraps.py
docker exec "$API_CID" python -c 'from controllers.common import wraps; assert hasattr(wraps, "_is_console_roster_agent_content_access_allowed"); print(wraps.__file__)'
docker exec "$WS_CID" python -c 'from controllers.common import wraps; assert hasattr(wraps, "_is_console_roster_agent_content_access_allowed"); print(wraps.__file__)'
docker-compose ps api api_websocket
```

Both hashes must equal `patched_sha256` in `manifest.txt`; the fresh imports
prove each new process can load the patched helper. This does not replace the
separate two-account functional acceptance in `test-plan.md`.

## Roll back

Restore the saved Compose file or remove only the two added mount entries, then
run the same existing Compose function:

```sh
docker-compose up -d --no-deps --force-recreate api api_websocket
API_CID=$(docker-compose ps -q api)
WS_CID=$(docker-compose ps -q api_websocket)
docker exec "$API_CID" sha256sum /app/api/controllers/common/wraps.py
docker exec "$WS_CID" sha256sum /app/api/controllers/common/wraps.py
docker exec "$API_CID" python -c 'from controllers.common import wraps; print(wraps.__file__)'
docker exec "$WS_CID" python -c 'from controllers.common import wraps; print(wraps.__file__)'
```

The hashes should return to the image's original
`a55bde316d9550353d2f2b4f3c9aa83f9085cbe34cc1f01767d50c6b11c11d9c`. Do not
delete the existing per-Agent whitelist row as part of this rollback; it is
independent data and can be audited separately.

## Local component tests

After preparation, the focused suite uses a uniquely named temporary
`postgres:15-alpine` container and the supplied API image. It removes the
temporary container and network on exit and stubs only the external RBAC
response:

```sh
./run-component-tests.sh "$API_IMAGE_ID" "$AGENT_FIX_OUTPUT_DIR"
```

The suite covers real PostgreSQL Agent/App rows, tenant/scope/status/source
boundaries, the three content scenes, live grant/revoke, explicit App grants,
console versus OpenAPI/non-console/no-request-context, non-content scenes, and
RBAC-disabled behavior.

## Runtime acceptance

After installation, test one member with `agent.manage` and one without it,
using an old and a newly created or copied roster Agent whose resource
whitelist excludes the manager. Confirm list, open, edit/save/refresh, and
debug/test for the manager; confirm denial for the non-manager unless an
existing explicit App grant applies. Also check a workflow-only Agent,
published WebApp/Backend API, API-key/release controls, and a service restart.
Record only redacted status, endpoint/method, image/module hashes, and the
result. Until this closed-host evidence is returned, the overall requirement
remains `PARTIAL`.
