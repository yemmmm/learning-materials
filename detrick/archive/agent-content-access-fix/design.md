# Agent content access fix — functional design

Status: design draft for plan review

Requirement: `detrick/archive/agent-content-access-fix/requirement.md`

## Problem and outcome

The `/agents` page is already gated by the workspace `agent.manage` permission, but
some content requests for a roster Agent continue through an App-scoped RBAC check.
That check consults the Agent's resource whitelist and returns 403 even when the
requesting member can open the Agents page. Adding the member to each Agent's
whitelist is a persistent data workaround; it does not implement the intended
workspace rule and does not cover future Agents.

After this change, a member who has `agent.manage` in the current workspace can
view, edit, and debug every active roster Agent in that workspace, regardless of
the Agent's App resource whitelist. The decision is evaluated on every request,
so a role grant or revocation takes effect without a data migration or scheduled
backfill.

## Goals

- Apply the workspace `agent.manage` decision to roster-Agent content operations
  at request time.
- Cover existing, newly created, and copied roster Agents without changing their
  stored access-policy rows.
- Inventory all backend surfaces used by the `/agents/<id>` editor, and apply the
  shortcut to the confirmed common App-gate content reads, writes, and
  debug/test conversations or logs while preserving existing workspace/legacy
  guard behavior on the other surfaces.
- Preserve tenant isolation and require an active roster Agent before the special
  grant is considered.
- Keep the current Agent list gate and the normal authentication, account,
  setup, license, and legacy edit checks.
- Deliver a version-checked, reversible deployment patch that can be installed
  into the existing Compose deployment without rebuilding the complete Dify image.

## Non-goals and unchanged behavior

- Do not rewrite or bulk-populate Agent resource whitelists. Existing rows remain
  available for audit and rollback.
- Do not grant access to WebApp or Backend API callers, published access, API
  keys, or other release/channel settings.
- Do not broaden Agent deletion or publishing beyond the permissions those routes
  already require. The requirement's minimum scope is content view, edit, and
  debug; any route inventory must leave deletion/publish behavior unchanged.
- Do not change workflow-only Agents. They remain governed by their parent
  workflow/App rules and are excluded from the roster special case.
- Do not change workflow, snippet, knowledge-base, dataset, or ordinary App
  authorization.
- Do not add a background migration, member enumeration, ACL backfill, new role,
  or new UI access-control model.

## Functional contract

For each request that reaches the patched common App-scoped gate:

1. Authenticate the account and resolve the current tenant as today.
2. Resolve the target Agent using the request's Agent identifier and the current
   tenant. The special path is eligible only when the Agent is active and has
   roster scope. A missing, inactive, or workflow-only Agent does not receive the
   special grant.
3. Ask the RBAC service for the caller's current workspace-level
   `agent.manage` permission. The check must omit a resource ID and must use the
   current tenant/account pair.
4. If that workspace decision is allowed, permit the targeted content operation
   without requiring the caller's account ID in the Agent resource whitelist and
   without requiring an additional App-scoped view/edit/test permission.
5. If it is not allowed, preserve the existing authorization path. This preserves
   any explicitly granted App access for members who do not have `agent.manage`
   and avoids silently revoking unrelated existing access. Revoking
   `agent.manage` therefore stops only the new workspace shortcut; an existing
   resource grant or maintainer short-circuit continues to follow its original
   rules.

Requests handled by the existing workspace-gated or legacy-gated route classes
do not receive a new decision in this patch; their current behavior is the
baseline that the route inventory and regression tests preserve.

The content scene set is the concrete set used by the current roster-Agent
editor and debug routes: `APP_VIEW_LAYOUT`, `APP_EDIT`, and `APP_TEST_AND_RUN`.
The implementation must not treat every App permission as an Agent-content
permission.

The rule applies to the console UI's direct backend requests that reach the
common App-scoped RBAC gate. The current route inventory has three distinct
classes, and the patch must preserve that distinction:

- **Common App gate (patched):** routes such as the Agent chat-message/history
  reads, build-chat finalization, and audio/runtime checks that call
  `rbac_permission_required(APP, ...)` or `enforce_rbac_access(...)` with one
  of the three content scenes. These receive the console roster shortcut.
- **Existing workspace gate (unchanged):** the Agents list and routes that
  already check workspace `agent.manage`. Their current guard remains the
  authority and needs no duplicate shortcut.
- **Legacy/login/edit/tenant guard (unchanged):** Agent config-inspector,
  drive, sandbox, detail, and build-draft surfaces that currently rely on
  their existing login/edit/tenant checks rather than the common App gate.
  This requirement does not retrofit them or turn their existing baseline
  behavior into a new universal deny rule.

Workflow-only, published-channel, API-key, deletion, and publishing routes
remain out of the special path. Revocation tests for the new shortcut apply to
the patched Common App gate class; the other classes are compared with their
pre-change behavior.

## Authorization boundaries

The special grant is made only when all of these are true:

| Boundary | Required condition |
| --- | --- |
| Tenant | Agent and caller are evaluated under the current tenant; a foreign-tenant Agent never qualifies. |
| Agent kind | `Agent.scope == ROSTER`, `Agent.source in APP_BACKED_AGENT_SOURCES`; workflow-only Agents do not qualify. |
| Agent state | The Agent is active, and the normal backing-resource resolution still applies. |
| Caller | The caller has current workspace `agent.manage`. |
| Operation | The route is an identified roster content view, edit, or debug/test operation. |
| Request origin | The shortcut requires `has_request_context()` and `request.blueprint == "console"`; OpenAPI and non-request callers never enter it. |
| RBAC state | With RBAC disabled, existing no-op behavior is retained; with RBAC enabled, the workspace decision is live. |

The target is identified from a trusted route `agent_id` wherever possible. A
route carrying only `app_id` must not infer the special grant unless its service
has already resolved that App to an active roster Agent in the same tenant. This
prevents an ordinary App or workflow-backed App from accidentally entering the
roster path.

## Implementation shape

Keep the patch to the common authorization boundary. The route inventory is
still required to prove which surfaces are patched, unchanged workspace-gated,
unchanged legacy-gated, or out of scope; it is not a request to retrofit every
Agent endpoint.

1. In the common RBAC enforcement path, add a narrow helper that first requires
   `has_request_context()` and an exact `request.blueprint == "console"` match.
   It then recognizes an Agent request, loads the tenant-filtered Agent, and checks
   `scope == ROSTER`, `source in APP_BACKED_AGENT_SOURCES`, `status == ACTIVE`,
   and the Agent's own `app_id == resource_id`. For an eligible content scene,
   query workspace `AGENT_MANAGE` before the current App resource check. An
   allowed result short-circuits only the App whitelist/permission decision.
   When a request has `agent_id`, resolve the actual roster Agent directly;
   never use a workflow-only parent or hidden runtime backing App as proof that
   the target is a roster Agent.
2. Keep the existing roster route guards, legacy edit checks, and the Agents page
   contract. The reviewed route inventory classifies the list as an existing
   workspace gate, config-inspector/drive/sandbox/detail/build-draft surfaces as
   legacy guards, and the chat/build-chat/audio content surfaces as the common
   App gate. This requirement needs no frontend patch or per-route permission
   rewrite. Keep publish, delete, API access, and API-key routes on their
   current permission stack; in particular, do not replace
   `APP_RELEASE_AND_VERSION` with the content shortcut.
3. Inspect the Agents page data requests and route list for resource filtering.
   The backend list must return all active roster Agents for a caller who passes
   the workspace gate. No client-side whitelist filter may hide those items.
   A frontend change is required only if a future route inventory contradicts
   the current source evidence.
4. Keep the patch compatible with the exact deployed API image. Before writing
   any file, compare the target module fingerprint and key context against the
   running 3.12.1 image. Refuse to patch an unknown file. Persist the patched
   module on the host and bind-mount it into the API and websocket containers
   using the deployment's existing Compose stack; do not reconstruct the stack,
   replace volumes, print secrets, or modify unrelated services. Restart only
   affected services and retain an explicit removal/restore procedure.

The common module is the only expected production change because the observed
failure is the same App-scoped gate used by multiple console content requests
and the current list/frontend paths already use workspace `agent.manage`. The
blueprint guard is essential because the same helper serves OpenAPI. It must not
be used as a blanket "all Agent paths are allowed" switch; the request origin,
Agent query, source, scene set, tenant, status, and resource-id match remain
explicit.

## Error behavior

- Missing or invalid Agent: preserve the route's existing not-found/validation
  response; do not convert it to an authorization success.
- Foreign tenant or workflow-only Agent: do not apply the special grant; let the
  normal route resolution and authorization behavior decide the response.
- Caller without `agent.manage`: on the patched Common App gate class, preserve
  existing App whitelist behavior and its 403 response where no explicit App
  access exists. On existing workspace/legacy guard classes, preserve the
  baseline route behavior rather than adding a new denial rule.
- RBAC service unavailable or returns an error: preserve the current failure
  behavior; do not fail open to the Agent special path.
- OpenAPI, non-console blueprints, and calls without a Flask request context:
  preserve the original App/resource authorization result.
- Version fingerprint mismatch during deployment: stop before writing or
  restarting any service and report the mismatch.

## Rollout and rollback

The deployment artifact is a small, version-checked source patch plus bounded
copyable shell blocks. Preparation must read the original module from the running
API image, verify its SHA/context, and write a host-persistent patched file.
Installation must add a bind mount to the existing Compose service definitions
for both the API and websocket processes, then restart only those services with
the deployment's existing Compose function/stack. The command must preserve
current environment files, profiles, networks, volumes, and service names.

Rollback is the inverse: stop/recreate the affected services after removing the
patch bind mount or restoring the saved original module, then verify the original
fingerprint and health. The data workaround previously applied to one Agent need
not be removed as part of this product fix; it is independent persisted data and
may remain until separately audited.

## Acceptance criteria

- A member with workspace `agent.manage` can list and open every active roster
  Agent in the same workspace even when the Agent whitelist excludes them,
  through the existing Agents list/workspace gate.
- On every patched Common App gate content route, the same member can load the
  editor/debug content and complete the covered save/test request with the
  whitelist excluded; a refreshed page retains the change. Existing legacy
  routes retain their pre-change behavior.
- The decision works for an existing Agent, a newly created Agent, and a copied
  Agent without adding whitelist rows, and stops working after `agent.manage` is
  revoked.
- A member without `agent.manage` cannot use the special path; existing explicit
  resource grants still behave as before.
- A workflow-only Agent, foreign-tenant target, inactive/unknown Agent, and
  ordinary App do not receive the special grant.
- WebApp/Backend API access, publish/API-key controls, deletion/publishing
  boundaries, workflow/knowledge-base permissions, and RBAC-disabled behavior
  remain unchanged.
- The patch is applied only to a fingerprint-matched 3.12.1 image, survives
  service restart, and can be removed with the documented rollback steps.
- Local component/integration tests pass, and the closed deployment has a
  separate runtime acceptance result for at least two accounts and old/new
  Agents. Until that evidence is returned, the overall requirement remains
  PARTIAL rather than complete.

## Redesign assumptions

1. The deployed 3.12.1 authorization module retains the public 60a18fa
   `enforce_rbac_access` shape and the `Agent` roster/status fields. If the
   fingerprint or import contract differs, the patch must be regenerated for
   that image before deployment.
2. The external RBAC service can answer a tenant-scoped workspace
   `agent_manage` check for the same account used by the existing App check. If
   it cannot, the implementation needs a deployment-specific adapter and this
   design must be revised.
3. The current `/agents` UI obtains its complete list from the workspace-gated
   roster endpoint and has no hidden resource-whitelist filter. If route/source
   review finds an additional filter or a second backend surface, add it to the
   reviewed route inventory and tests before implementation.

## Review dispositions

- **Finding 1 — invalid against the confirmed scope:** some Agent
  config-inspector, drive, sandbox, detail, and build-draft routes use only
  legacy/login/edit/tenant guards and do not reach the common App gate. The
  requirement adds a workspace shortcut to the confirmed Common App gate; it
  does not retrofit unrelated guards or impose a universal `agent.manage`
  denial. Their baseline behavior is preserved and tested as unchanged.
- **Finding 2 — accepted-high and addressed:** the common gate also serves
  OpenAPI. The design now requires `has_request_context()` and the exact
  `request.blueprint == "console"` condition before the roster shortcut; the
  shared plan compares identical App/scene requests through console, OpenAPI,
  non-console, and no-request-context paths.
