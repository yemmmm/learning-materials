from __future__ import annotations

from collections.abc import Iterator
import os
from uuid import uuid4

import pytest
from flask import Blueprint, Flask
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session
from werkzeug.exceptions import Forbidden

from configs import dify_config
from controllers.common import wraps as rbac_wraps
from core.rbac import RBACPermission, RBACResourceScope
from models.agent import Agent, AgentKind, AgentScope, AgentSource, AgentStatus
from models.enums import AppStatus
from models.model import App, AppMode


TENANT_ID = str(uuid4())
ACCOUNT_ID = str(uuid4())
ROSTER_AGENT_ID = str(uuid4())
ROSTER_APP_ID = str(uuid4())
WORKFLOW_AGENT_ID = str(uuid4())
WORKFLOW_APP_ID = str(uuid4())
INACTIVE_AGENT_ID = str(uuid4())
INACTIVE_APP_ID = str(uuid4())
OTHER_AGENT_ID = str(uuid4())
OTHER_APP_ID = str(uuid4())


@pytest.fixture()
def isolated_agent_session(monkeypatch: pytest.MonkeyPatch) -> Iterator[Session]:
    database_url = os.environ.get("AGENT_FIX_TEST_DATABASE_URL")
    if not database_url:
        pytest.fail("AGENT_FIX_TEST_DATABASE_URL must point to the unique temporary PostgreSQL database")
    engine = create_engine(database_url)
    App.__table__.create(engine, checkfirst=True)
    Agent.__table__.create(engine, checkfirst=True)
    session = Session(engine)
    monkeypatch.setattr(rbac_wraps.db, "session", session)
    monkeypatch.setattr(dify_config, "RBAC_ENABLED", True)
    session.execute(delete(Agent))
    session.execute(delete(App))
    session.commit()
    yield session
    session.execute(delete(Agent))
    session.execute(delete(App))
    session.commit()
    session.close()
    engine.dispose()


def add_agent(
    session: Session,
    *,
    tenant_id: str = TENANT_ID,
    agent_id: str = ROSTER_AGENT_ID,
    app_id: str = ROSTER_APP_ID,
    scope: AgentScope = AgentScope.ROSTER,
    source: AgentSource = AgentSource.AGENT_APP,
    status: AgentStatus = AgentStatus.ACTIVE,
) -> Agent:
    session.add(
        App(
            id=app_id,
            tenant_id=tenant_id,
            name=f"App {app_id}",
            description="",
            mode=AppMode.AGENT,
            status=AppStatus.NORMAL,
            enable_site=False,
            enable_api=False,
            max_active_requests=10,
            maintainer=str(uuid4()),
            use_icon_as_answer_icon=False,
        )
    )
    agent = Agent(
        id=agent_id,
        tenant_id=tenant_id,
        name=f"Agent {agent_id}",
        description="",
        role="",
        agent_kind=AgentKind.DIFY_AGENT,
        scope=scope,
        source=source,
        app_id=app_id,
        status=status,
    )
    session.add(agent)
    session.commit()
    return agent


def console_app() -> Flask:
    app = Flask(__name__)
    bp = Blueprint("console", __name__, url_prefix="/console/api")

    def enforce_agent(agent_id: str, scene: RBACPermission) -> str:
        rbac_wraps.enforce_rbac_access(
            tenant_id=TENANT_ID,
            account_id=ACCOUNT_ID,
            resource_type=RBACResourceScope.APP,
            scene=scene,
            path_args={"agent_id": agent_id},
        )
        return "allowed"

    @bp.get("/agent/<agent_id>")
    def agent_route(agent_id: str):
        return enforce_agent(agent_id, RBACPermission.APP_VIEW_LAYOUT)

    @bp.get("/agent/<agent_id>/<scene_name>")
    def agent_scene_route(agent_id: str, scene_name: str):
        return enforce_agent(agent_id, RBACPermission(scene_name))

    @bp.get("/app/<app_id>")
    def app_route(app_id: str):
        rbac_wraps.enforce_rbac_access(
            tenant_id=TENANT_ID,
            account_id=ACCOUNT_ID,
            resource_type=RBACResourceScope.APP,
            scene=RBACPermission.APP_VIEW_LAYOUT,
            path_args={"app_id": app_id},
        )
        return "allowed"

    @bp.get("/mismatch/<agent_id>/<app_id>")
    def mismatched_agent_route(agent_id: str, app_id: str):
        rbac_wraps.enforce_rbac_access(
            tenant_id=TENANT_ID,
            account_id=ACCOUNT_ID,
            resource_type=RBACResourceScope.APP,
            scene=RBACPermission.APP_VIEW_LAYOUT,
            path_args={"agent_id": agent_id, "app_id": app_id},
        )
        return "allowed"

    app.register_blueprint(bp)
    return app


def install_rbac_stub(monkeypatch: pytest.MonkeyPatch, *, agent_manage: bool, app_access: bool = False):
    calls: list[dict[str, object]] = []

    def check(tenant_id: str, account_id: str, **kwargs: object) -> bool:
        calls.append({"tenant_id": tenant_id, "account_id": account_id, **kwargs})
        if kwargs["scene"] == RBACPermission.AGENT_MANAGE:
            return agent_manage
        return app_access

    monkeypatch.setattr(rbac_wraps.RBACService.CheckAccess, "check", check)
    return calls


@pytest.mark.parametrize(
    "scene",
    [
        RBACPermission.APP_VIEW_LAYOUT,
        RBACPermission.APP_EDIT,
        RBACPermission.APP_TEST_AND_RUN,
    ],
)
def test_console_roster_manager_bypasses_app_whitelist(
    isolated_agent_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    scene: RBACPermission,
) -> None:
    add_agent(isolated_agent_session)
    calls = install_rbac_stub(monkeypatch, agent_manage=True)
    app = console_app()

    response = app.test_client().get(f"/console/api/agent/{ROSTER_AGENT_ID}/{scene.value}")
    assert response.status_code == 200

    assert calls == [
        {
            "tenant_id": TENANT_ID,
            "account_id": ACCOUNT_ID,
            "scene": RBACPermission.AGENT_MANAGE,
            "resource_type": None,
            "resource_id": None,
        }
    ]


def test_console_manager_is_evaluated_on_each_request_and_revoke_falls_back(
    isolated_agent_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_agent(isolated_agent_session)
    state = {"agent_manage": True}
    calls = []

    def check(_tenant_id: str, _account_id: str, **kwargs: object) -> bool:
        calls.append(kwargs)
        return state["agent_manage"] if kwargs["scene"] == RBACPermission.AGENT_MANAGE else False

    monkeypatch.setattr(rbac_wraps.RBACService.CheckAccess, "check", check)
    client = console_app().test_client()
    assert client.get(f"/console/api/agent/{ROSTER_AGENT_ID}").status_code == 200
    state["agent_manage"] = False
    assert client.get(f"/console/api/agent/{ROSTER_AGENT_ID}").status_code == 403

    assert [call["scene"] for call in calls] == [
        RBACPermission.AGENT_MANAGE,
        RBACPermission.AGENT_MANAGE,
        RBACPermission.APP_VIEW_LAYOUT,
    ]


def test_no_manager_preserves_explicit_app_grant(isolated_agent_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    add_agent(isolated_agent_session)
    calls = install_rbac_stub(monkeypatch, agent_manage=False, app_access=True)
    response = console_app().test_client().get(
        f"/console/api/agent/{ROSTER_AGENT_ID}/{RBACPermission.APP_EDIT.value}"
    )
    assert response.status_code == 200
    assert [call["scene"] for call in calls] == [RBACPermission.AGENT_MANAGE, RBACPermission.APP_EDIT]


@pytest.mark.parametrize(
    "agent_kwargs",
    [
        {
            "scope": AgentScope.WORKFLOW_ONLY,
            "source": AgentSource.WORKFLOW,
            "agent_id": WORKFLOW_AGENT_ID,
            "app_id": WORKFLOW_APP_ID,
        },
        {"status": AgentStatus.ARCHIVED, "agent_id": INACTIVE_AGENT_ID, "app_id": INACTIVE_APP_ID},
    ],
)
def test_workflow_or_inactive_agent_does_not_receive_roster_override(
    isolated_agent_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    agent_kwargs: dict[str, object],
) -> None:
    add_agent(isolated_agent_session, **agent_kwargs)
    calls = install_rbac_stub(monkeypatch, agent_manage=True)
    response = console_app().test_client().get(f"/console/api/agent/{agent_kwargs['agent_id']}")
    assert response.status_code == 403
    assert [call["scene"] for call in calls] == [RBACPermission.APP_VIEW_LAYOUT]


def test_foreign_tenant_and_mismatched_agent_id_do_not_grant(
    isolated_agent_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_agent(isolated_agent_session, tenant_id=str(uuid4()))
    calls = install_rbac_stub(monkeypatch, agent_manage=True)
    response = console_app().test_client().get(f"/console/api/agent/{ROSTER_AGENT_ID}")
    assert response.status_code == 403
    assert [call["scene"] for call in calls] == [RBACPermission.APP_VIEW_LAYOUT]

    add_agent(isolated_agent_session, agent_id=OTHER_AGENT_ID, app_id=OTHER_APP_ID)
    calls.clear()
    response = console_app().test_client().get(
        f"/console/api/mismatch/{ROSTER_AGENT_ID}/{OTHER_APP_ID}"
    )
    assert response.status_code == 403
    assert [call["scene"] for call in calls] == [RBACPermission.APP_VIEW_LAYOUT]


def test_app_id_only_route_requires_roster_ownership(isolated_agent_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    add_agent(isolated_agent_session)
    calls = install_rbac_stub(monkeypatch, agent_manage=True)
    response = console_app().test_client().get(f"/console/api/app/{ROSTER_APP_ID}")
    assert response.status_code == 200
    assert calls[0]["scene"] == RBACPermission.AGENT_MANAGE


def test_openapi_nonconsole_and_no_request_context_fall_through(
    isolated_agent_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_agent(isolated_agent_session)
    calls = install_rbac_stub(monkeypatch, agent_manage=True)
    app = Flask(__name__)
    for blueprint_name in ("openapi", "other"):
        bp = Blueprint(blueprint_name, f"{blueprint_name}-module", url_prefix=f"/{blueprint_name}")

        @bp.get("/agent/<agent_id>")
        def route(agent_id: str):
            with pytest.raises(Forbidden):
                rbac_wraps.enforce_rbac_access(
                    tenant_id=TENANT_ID,
                    account_id=ACCOUNT_ID,
                    resource_type=RBACResourceScope.APP,
                    scene=RBACPermission.APP_VIEW_LAYOUT,
                    path_args={"agent_id": agent_id},
                )
            return "denied"

        app.register_blueprint(bp)

    client = app.test_client()
    assert client.get(f"/openapi/agent/{ROSTER_AGENT_ID}").data == b"denied"
    assert client.get(f"/other/agent/{ROSTER_AGENT_ID}").data == b"denied"
    assert all(call["scene"] == RBACPermission.APP_VIEW_LAYOUT for call in calls)
    assert all(call["scene"] != RBACPermission.AGENT_MANAGE for call in calls)

    # The helper itself is safe outside Flask; it must not call the workspace
    # RBAC endpoint or provide an implicit App grant.
    calls.clear()
    assert not rbac_wraps._is_console_roster_agent_content_access_allowed(
        tenant_id=TENANT_ID,
        account_id=ACCOUNT_ID,
        resource_type=RBACResourceScope.APP,
        resource_id=ROSTER_APP_ID,
        scene=RBACPermission.APP_VIEW_LAYOUT,
        path_args={"agent_id": ROSTER_AGENT_ID},
    )
    assert calls == []


def test_non_content_scene_and_rbac_disabled_keep_baseline(
    isolated_agent_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_agent(isolated_agent_session)
    calls = install_rbac_stub(monkeypatch, agent_manage=True)
    response = console_app().test_client().get(
        f"/console/api/agent/{ROSTER_AGENT_ID}/{RBACPermission.APP_RELEASE_AND_VERSION.value}"
    )
    assert response.status_code == 403
    assert [call["scene"] for call in calls] == [RBACPermission.APP_RELEASE_AND_VERSION]

    monkeypatch.setattr(dify_config, "RBAC_ENABLED", False)
    response = console_app().test_client().get(f"/console/api/agent/{ROSTER_AGENT_ID}")
    assert response.status_code == 200
    assert len(calls) == 1
