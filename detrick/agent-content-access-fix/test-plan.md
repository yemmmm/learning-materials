# Agent content access fix — shared test plan

Status: plan draft for plan review

Requirement: `detrick/agent-content-access-fix/requirement.md`

This is the single shared plan for developer checks and independent test rounds.
Later rounds append results to this file; they do not replace earlier evidence.

## Test fixtures and identities

Use an isolated temporary database and an isolated API test container based on
the available `langgenius/dify-ee-api:3.12.0` image for local component tests.
The image has Python 3.12, pytest, Flask, psycopg2, SQLAlchemy, and can import
the common RBAC module without starting the full application. Use a mock only
for the external `RBACService.CheckAccess` response; use real SQLAlchemy Agent
rows and the real authorization helper for boundary decisions.

Fixtures should include:

- one tenant with two accounts: `agent_manager` (workspace `agent.manage`) and
  `ordinary_member` (no `agent.manage`);
- an active roster Agent with a specific whitelist that excludes both test
  accounts, plus its normal backing App;
- an active newly created roster Agent and a copied roster Agent, both with the
  same excluded whitelist;
- a workflow-only Agent/backing App in the same tenant;
- an active roster Agent in a second tenant and an inactive/unknown Agent case;
- explicit App resource permission for one ordinary-member control case;
- published WebApp/Backend API and API-key fixtures if the route suite can use
  them without coupling to the external deployment.

Every fixture created for a test must live in a unique temporary database/schema
or be removed after the test. Never use the deployed Dify database.

## Route and source inventory gate

Before declaring implementation ready, record the actual backend routes and
frontend requests used by `/agents`, `/agents/<id>`, editor save, build/config,
debug/test conversation, logs, and content file/skill operations. For each route
record its identifier source (`agent_id`, `app_id`, or workflow node), current
decorators, content scene, and whether it is in scope.

The inventory must classify every discovered route into one of these classes:

- **Common App gate (patched):** Agent chat-message/history, build-chat
  finalization, audio/runtime, and any other route that actually calls the
  common App-scoped gate with `APP_VIEW_LAYOUT`, `APP_EDIT`, or
  `APP_TEST_AND_RUN`.
- **Existing workspace gate (unchanged):** the Agents list and routes already
  checking workspace `agent.manage`.
- **Legacy/login/edit/tenant guard (unchanged):** config-inspector, drive,
  sandbox, detail, build-draft, or other routes that do not reach the common
  App gate today.
- **Out of scope:** workflow-only, workflow composer, published channel,
  API-key, delete, and publish routes.

The inventory must then prove:

- the list is gated by workspace `agent.manage` and is not filtered by resource
  whitelist;
- every patched Common App gate route is covered by the strict console
  shortcut, while existing workspace and legacy classes retain their current
  guards and behavior;
- workflow-only, workflow composer, published channel, API-key, delete, and
  publish routes retain their intended existing checks;
- no frontend permission atom hides a roster Agent after the list response.

If inventory discovers a second path, add it to the matrix below and to the
implementation before the plan review gate closes.

## Authorization decision matrix

For each applicable content route, assert the result below. A successful
response may be a normal 2xx/stream response; a denied response must preserve
the route's existing 403/404 behavior.

| Case | Target | Caller/permission | Whitelist | Expected |
| --- | --- | --- | --- | --- |
| A1 | same-tenant active roster Agent on patched Common App route | `agent_manager` has `agent.manage` | excludes caller | allow covered view, edit, debug scenes |
| A2 | same patched route after role grant | caller newly gains `agent.manage` | excludes caller | allow on next request, no migration |
| A3 | same patched Common App route after role revoke | caller loses `agent.manage` | excludes caller | special grant stops on next request; existing resource/maintainer rules remain |
| A4 | patched Common App route | ordinary member, no App grant | excludes caller | deny as before |
| A5 | patched Common App route | ordinary member with explicit App grant | excludes caller | preserve existing explicit grant |
| A6 | newly created roster Agent on patched route | `agent_manager` | excludes caller | allow |
| A7 | copied roster Agent on patched route | `agent_manager` | excludes caller | allow |
| A8 | workflow-only Agent | `agent_manager` | any | no roster override; parent workflow rule applies |
| A9 | same ID under foreign tenant | `agent_manager` in current tenant | any | no cross-tenant grant; route resolution/deny remains bounded |
| A10 | inactive/unknown Agent | `agent_manager` | any | no grant; existing not-found/deny behavior |
| A11 | ordinary App or dataset | `agent_manager` | any | unchanged ordinary resource authorization |
| A12 | same roster Agent with RBAC disabled | any authenticated caller | any | preserve existing RBAC-disabled behavior |
| A13 | same App ID and content scene through OpenAPI | any caller | excludes caller | preserve original OpenAPI resource authorization; no workspace shortcut |
| A14 | same App ID and scene in a non-console blueprint or without request context | any caller | excludes caller | preserve original authorization; no workspace shortcut |

## Component tests

Add focused tests at the common authorization boundary, using the real Agent
model query and a stubbed external RBAC response:

1. `agent_id` resolves to an active `ROSTER` Agent whose source is in
   `APP_BACKED_AGENT_SOURCES`, workspace check returns allowed, and an App
   `APP_VIEW_LAYOUT`, `APP_EDIT`, or `APP_TEST_AND_RUN` check returns without
   consulting the App whitelist.
2. Workspace check returns denied and the existing App check is still evaluated;
   verify no fail-open path.
3. The Agent query is tenant-scoped and excludes workflow-only, inactive, and
   missing rows.
4. A route carrying only `app_id` does not enter the special path unless its
   trusted service resolution proves an active app-backed roster Agent in the
   same tenant whose own `Agent.app_id` equals the checked resource ID.
   An `agent_id` route must resolve the actual Agent instead of treating a
   workflow-only parent or hidden runtime backing App as a roster target.
5. RBAC disabled remains a no-op.
6. Repeated requests re-evaluate the workspace decision; no cached member list
   or data backfill is used.
7. With the same tenant/account/App ID/scene, a Flask `console` request can use
   the roster shortcut, while an OpenAPI request, a different blueprint, and a
   call outside a Flask request context use the original resource check.

Use call assertions to prove the workspace check has no resource ID and that a
successful roster override does not call the resource whitelist check. Do not
claim cross-tenant 403 solely from the helper if the unchanged route resolver
normally returns 404; assert the no-grant and tenant-bounded result instead.

## API/component route tests

Exercise representative real handlers in the isolated API container:

- Agents list and Agent detail read;
- chat-message/history read that previously returned 403;
- editor/composer draft read and save;
- build-draft checkout/apply or equivalent current config write;
- debug conversation refresh and debug/test/log read;
- any agent-drive content read/write route found by the route inventory.

For `agent_manager`, each patched Common App gate route must succeed against the
excluded whitelist. Existing workspace-gated and legacy-gated routes must match
their pre-change result; they are not converted into a new universal
`agent.manage` denial rule. For `ordinary_member`, the special path must not
allow access on patched routes. For the explicit-App-grant control, preserve the
prior result. Verify saved content survives a new session or handler request.

## Regression and boundary tests

Run the following at stable implementation state:

- same tenant versus foreign tenant;
- roster versus workflow-only Agent;
- active versus inactive/unknown Agent;
- existing, new, and copied roster Agents;
- grant and revoke `agent.manage` between requests;
- resource whitelist contains caller versus excludes caller;
- `APP_VIEW_LAYOUT`, `APP_EDIT`, and `APP_TEST_AND_RUN` separately;
- RBAC enabled versus disabled;
- existing workspace-gated and legacy-gated Agent routes versus their recorded
  baseline behavior;
- console versus OpenAPI/non-console/no-request-context calls using the same
  App ID and scenes, proving the new shortcut cannot cross the API boundary;
- non-target ordinary App, workflow, dataset/knowledge-base, and snippet paths;
- published WebApp and Backend API calls, API-key list/create/delete, and
  delete/publish controls, proving they retain the pre-change result;
- service restart/reimport after the patch, proving the persistent mounted file
  is the one loaded by API and websocket processes.

## Deployment and rollback checks

Use the user's existing Compose directory and invocation mechanism. Do not
reconstruct the stack from a guessed file or touch the deployed database.

Preparation checks:

1. Read the common module from the running API image.
2. Verify the expected 3.12.1 image/module fingerprint and key context.
3. Abort before writes/restarts on a mismatch.
4. Produce a host-persistent patched module and an original backup with bounded
   permissions and no secrets in output.

Installation checks:

1. Confirm the bind mount is present in both API and websocket service configs.
2. Restart only the affected services through the existing Compose stack.
3. Check container health, import the patched module, and issue a harmless
   authorization probe.
4. Confirm the unrelated worker/beat/collector services and existing volumes,
   env files, networks, and profiles remain unchanged.

Rollback checks:

1. Remove the patch mount or restore the saved original module using the inverse
   bounded commands.
2. Recreate only affected services.
3. Verify the original fingerprint/import and that the special grant no longer
   applies.
4. Preserve any pre-existing per-Agent whitelist data; do not delete it as part
   of rollback.

## Closed-environment runtime acceptance

The user must run the version-checked patch in the EE 3.12.1 deployment and
report evidence for at least two accounts: one with `agent.manage` and one
without it. Use one old and one newly created/copied roster Agent, each with the
manager absent from the resource whitelist. For the manager, verify list, open,
edit/save/refresh, and debug/test. For the non-manager, verify denial unless an
existing explicit resource grant applies. Verify a workflow-only Agent,
published WebApp/Backend API, API-key/release controls, and service restart.

Record exact image/module fingerprints, service names, endpoint/method, status,
and redacted response reason. Do not include cookies, tokens, passwords, or
connection strings. Until this evidence is returned, status is `PARTIAL` even
if local component tests pass.

## Cleanup and completion gates

At the end of each local round, remove only uniquely owned temporary containers,
schemas, files, and logs. Leave the isolated Postgres image/cache intact if it
is shared. Do not alter the closed deployment during local testing.

Completion requires all of the following:

- route/source inventory is attached to the implementation review;
- component and route tests pass with no mock-only claim for database/tenant
  behavior;
- regression matrix passes, including non-target and rollback checks;
- independent tester appends a PASS round to this same file;
- closed EE 3.12.1 runtime acceptance is returned and redacted;
- any failed or blocked case remains recorded with disposition;
- the version-checked patch, persistent deployment steps, and inverse rollback
  are documented and committed with no unrelated files.

## Round log

### Round 0 — plan baseline

Not executed. This document defines the cases for the developer and independent
tester. The local image is available for the planned component container; the
remote EE 3.12.1 runtime is not yet verified.
