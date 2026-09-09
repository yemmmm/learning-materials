# Agent route inventory

This inventory is based on the API module source extracted from the available
`langgenius/dify-ee-api:3.12.0` image. Its
`controllers/common/wraps.py` is byte-identical to the public 60a18fa baseline
(`a55bde316d9550353d2f2b4f3c9aa83f9085cbe34cc1f01767d50c6b11c11d9c`). The
closed 3.12.1 image must pass the same fingerprint check before installation.
Line numbers below identify the classes/decorators in that source; they are
source evidence rather than a claim about the unverified closed image.

## Page gate and list data

| Surface | Source behavior | Result |
| --- | --- | --- |
| `/agents` page | `web/app/(commonLayout)/agents/agents-access-guard.tsx` calls `useCanManageAgents`; the guard is workspace `agent.manage` | unchanged |
| `GET /console/api/agent` | `controllers/console/agent/roster.py:557-592`, `AgentAppListApi`, workspace `AGENT_MANAGE`, `resource_required=False` | unchanged workspace gate |
| roster list query | `AgentRosterService._build_roster_agents_stmt` filters only current `tenant_id`, `scope=ROSTER`, and `status=ACTIVE`; `AppService` Agent mode does not apply an App whitelist | all eligible roster Agents are returned after the page gate |
| `/agents/<id>/config` channel settings | WebApp/Backend API publication controls; route inventory does not treat these as Agent content ACLs | publication/channel rules unchanged |

No frontend resource-whitelist atom was found in the Agent v2 permission
module. The page gate and the roster list already express the requested
workspace rule, so no frontend or list patch is included.

## Common App gate: patched shortcut

The patch is reached only from `controllers/common/wraps.py` after the normal
resource ID is resolved and after the existing App maintainer short-circuit.
It requires the Flask request context, exact `request.blueprint == "console"`,
a tenant-scoped active `Agent` with `scope=ROSTER`, an
`APP_BACKED_AGENT_SOURCES` source, and matching `Agent.app_id`. Only these
scenes use the workspace shortcut:

| Route and handler | Existing App scene | Identifier path | Classification |
| --- | --- | --- | --- |
| `GET /console/api/agent/<agent_id>/chat-messages`, `message.py:164-186`, `AgentChatMessageListApi.get` | `APP_VIEW_LAYOUT` | `agent_id`, resolved runtime App | patched |
| `POST /console/api/agent/<agent_id>/chat-messages`, `completion.py:251-278`, `AgentChatMessageApi.post` | `APP_TEST_AND_RUN` | `agent_id`, resolved runtime App | patched |
| `POST /console/api/agent/<agent_id>/build-chat/finalize`, `completion.py:281-307`, `AgentBuildChatFinalizeApi.post` | `APP_TEST_AND_RUN` | `agent_id`, resolved runtime App | patched |
| `POST /console/api/agent/<agent_id>/audio-to-text`, `audio.py:207-246`, `AgentChatMessageAudioApi.post` | explicit `enforce_rbac_access(APP_TEST_AND_RUN)` | service resolves App and passes `app_id`; helper proves the same active roster Agent owns that App | patched |

For the `app_id`-only audio call, the helper queries the current tenant for an
active app-backed roster Agent whose own `Agent.app_id` equals the checked App.
It does not use a workflow-only parent or a hidden backing App as proof of
roster ownership. When the workspace check is denied, the original App
resource check still runs, preserving explicit App grants and their 403 path.

## Existing workspace gate: unchanged

These routes already require workspace `AGENT_MANAGE`; the patch does not
replace or weaken that decorator:

| Surface | Source |
| --- | --- |
| roster list/create | `roster.py:557-621` |
| Agent detail read/update | `roster.py:622-678` |
| publish | `roster.py:719-742` |
| build-draft checkout/read/apply | `roster.py:743-840` |
| copy | `roster.py:841-870` |
| API access and API-key routes | `roster.py:871-959` |
| logs/statistics/versions/restore | `roster.py:983-1162` |
| Agent composer | `composer.py:462-500`; it keeps both App edit and workspace Agent gates |

Delete, publish, API access, API-key, logs, statistics, and version controls
retain their existing permission stack. In particular, the patch does not
turn `APP_RELEASE_AND_VERSION` into a content permission.

## Legacy/login/edit/tenant gate: unchanged

The following Agent-id routes resolve the Agent/runtime App or use the existing
edit guard but do not call the common App RBAC gate in the inspected source:

- Agent message feedback, suggested questions, and message detail;
- Agent config inspector, drive inspector, and sandbox file/skill operations;
- Agent debug-conversation refresh;
- Agent skill/drive mutations that use the existing service-level guard.

They are intentionally not retrofitted by this common-boundary patch. With
RBAC enabled, the existing `edit_permission_required` path retains its
baseline behavior; it is not turned into a universal new denial rule.

## Out of scope

Workflow-only Agent rows, workflow Agent composer routes, ordinary App,
dataset/knowledge-base, snippet, published WebApp/Backend API, API-key,
delete, and publish authorization remain on their existing paths. OpenAPI
uses the same common helper module but does not receive the shortcut because
the helper requires the exact `console` blueprint. Calls outside a Flask
request context and non-console blueprints also fall through to the original
resource check.
