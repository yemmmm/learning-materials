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

Copy this directory to the host and run these commands in the existing shell.
Use the exact API image tag already used by the deployment; do not guess a
different image or include credentials in command output.

```sh
export AGENT_FIX_API_IMAGE='your-registry/dify-ee-api:3.12.1'
export AGENT_FIX_OUTPUT_DIR='/absolute/path/agent-content-access-fix-applied'
./prepare-agent-content-fix.sh "$AGENT_FIX_API_IMAGE" "$AGENT_FIX_OUTPUT_DIR"
cat "$AGENT_FIX_OUTPUT_DIR/manifest.txt"
```

Preparation reads the module from the image, checks the expected SHA-256, and
stops before producing a patched module when the bytes differ. It then compiles
the patched source with the image's Python 3.12 interpreter. Preparation does
not start a service and does not connect to the Dify database.

Expected source hash for the reviewed 3.12.1-compatible baseline:

```text
a55bde316d9550353d2f2b4f3c9aa83f9085cbe34cc1f01767d50c6b11c11d9c
```

If the hash check fails, stop and regenerate the patch against that exact
image. Do not overwrite the module by hand.

## Install using the existing Compose stack

The preparation directory contains
`agent-content-access.override.yml`, which adds the same read-only host mount
to `api` and `api_websocket`. Set the variable before Compose interpolation:

```sh
export AGENT_FIX_OUTPUT_DIR='/absolute/path/agent-content-access-fix-applied'
```

First record the current source hash from both serving containers through the
existing Compose invocation. Both must be the expected original hash (or an
already documented, identical preparation state) before installation; an
unknown current hash is a stop condition.

```sh
API_CID=$(docker-compose [existing-compose-args] ps -q api)
WS_CID=$(docker-compose [existing-compose-args] ps -q api_websocket)
docker exec "$API_CID" sha256sum /app/api/controllers/common/wraps.py
docker exec "$WS_CID" sha256sum /app/api/controllers/common/wraps.py
```

Use the deployment's existing `docker-compose` shell function and its usual
project/file/environment arguments. The safest installation is to add the
following one read-only volume line to each already-loaded service definition,
keeping every existing `volumes` entry and saving a copy of the Compose file:

```yaml
services:
  api:
    volumes:
      - /absolute/path/agent-content-access-fix-applied/wraps.patched.py:/app/api/controllers/common/wraps.py:ro
  api_websocket:
    volumes:
      - /absolute/path/agent-content-access-fix-applied/wraps.patched.py:/app/api/controllers/common/wraps.py:ro
```

Then run the deployment's normal `up -d --no-deps --force-recreate api
api_websocket` command through that same shell function. Do not rebuild the
full image or recreate workers, beat, collector, databases, networks, or
volumes.

If the existing function explicitly supports an additional Compose file, the
generated override may be supplied as its final `-f` file. Preserve all of the
function's existing arguments; do not invoke Compose with only the override,
because that would omit the deployment's base files:

```sh
docker-compose [existing-compose-args] -f "$AGENT_FIX_OUTPUT_DIR/agent-content-access.override.yml" config --services
docker-compose [existing-compose-args] -f "$AGENT_FIX_OUTPUT_DIR/agent-content-access.override.yml" config | grep -A4 -E '^  (api|api_websocket):'
docker-compose [existing-compose-args] -f "$AGENT_FIX_OUTPUT_DIR/agent-content-access.override.yml" up -d --no-deps --force-recreate api api_websocket
```

The effective mount must be exactly:

```text
AGENT_FIX_OUTPUT_DIR/wraps.patched.py:/app/api/controllers/common/wraps.py:ro
```

After the recreate, use the same Compose invocation to obtain the two container
IDs and verify the mounted file hash. Replace the placeholders with the normal
Compose arguments used at the site:

```sh
API_CID=$(docker-compose [existing-compose-args] -f "$AGENT_FIX_OUTPUT_DIR/agent-content-access.override.yml" ps -q api)
WS_CID=$(docker-compose [existing-compose-args] -f "$AGENT_FIX_OUTPUT_DIR/agent-content-access.override.yml" ps -q api_websocket)
docker exec "$API_CID" sha256sum /app/api/controllers/common/wraps.py
docker exec "$WS_CID" sha256sum /app/api/controllers/common/wraps.py
docker-compose [existing-compose-args] -f "$AGENT_FIX_OUTPUT_DIR/agent-content-access.override.yml" ps api api_websocket
```

Both hashes must equal the `patched_sha256` in `manifest.txt`. This proves the
mounted source is loaded by both serving processes; it does not replace the
separate two-account functional acceptance in `test-plan.md`.

## Roll back

Remove the override from the Compose invocation, or remove only the two mount
entries restored from the saved Compose copy. Recreate the same two services
through the existing stack command:

```sh
docker-compose [existing-compose-args] up -d --no-deps --force-recreate api api_websocket
API_CID=$(docker-compose [existing-compose-args] ps -q api)
WS_CID=$(docker-compose [existing-compose-args] ps -q api_websocket)
docker exec "$API_CID" sha256sum /app/api/controllers/common/wraps.py
docker exec "$WS_CID" sha256sum /app/api/controllers/common/wraps.py
```

The hashes should return to the image's original
`a55bde316d9550353d2f2b4f3c9aa83f9085cbe34cc1f01767d50c6b11c11d9c`. Do not
delete the existing per-Agent whitelist row as part of this rollback; it is
independent data and can be audited separately.

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
