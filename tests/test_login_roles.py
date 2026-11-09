from datetime import datetime, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from sys import modules
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

APP_DIR = Path(__file__).resolve().parents[1] / "backend" / "KulcskezeloApp" / "app"


def _load(name, path, dependencies):
    with patch.dict(modules, dependencies):
        spec = spec_from_file_location(name, path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def _user(roles, active=True, password_ok=True):
    return SimpleNamespace(
        id=7,
        is_active=active,
        roles=[SimpleNamespace(name=name) for name in roles],
        check_password=lambda password: password_ok,
    )


@pytest.fixture
def auth_env():
    session = MagicMock()
    audit = MagicMock()
    jwt = MagicMock()
    jwt.encode.return_value = "signed-token"
    user_model = MagicMock()

    dependencies = {
        "app": ModuleType("app"),
        "app.blueprints": ModuleType("app.blueprints"),
        "app.blueprints.reports": ModuleType("app.blueprints.reports"),
        "app.blueprints.reports.service": ModuleType("app.blueprints.reports.service"),
        "app.extensions": ModuleType("app.extensions"),
        "app.models": ModuleType("app.models"),
        "app.models.role": ModuleType("app.models.role"),
        "app.models.user": ModuleType("app.models.user"),
        "authlib": ModuleType("authlib"),
        "authlib.jose": ModuleType("authlib.jose"),
    }
    dependencies["app.blueprints.reports.service"].create_audit_log = audit
    dependencies["app.extensions"].db = SimpleNamespace(session=session)
    dependencies["app.models.role"].Role = MagicMock()
    dependencies["app.models.user"].User = user_model
    dependencies["authlib.jose"].jwt = jwt

    app = Flask("auth-tests")
    app.config["PRIVATE_KEY"] = b"key"

    with app.app_context():
        module = _load(
            "auth_service_under_test",
            APP_DIR / "blueprints/auth/service.py",
            dependencies,
        )
        yield SimpleNamespace(
            service=module.AuthService,
            user_model=user_model,
            audit=audit,
            jwt=jwt,
            session=session,
        )


def _login(env, user, **extra):
    env.user_model.query.filter_by.return_value.first.return_value = user
    return env.service.login({"email": "a@b.hu", "password": "pw", **extra})


def test_single_role_logs_in_directly(auth_env):
    ok, res = _login(auth_env, _user(["Instructor"]))

    assert ok is True
    assert res["token"] == "signed-token"
    assert res["role"] == "Instructor"
    assert auth_env.jwt.encode.call_args.args[1]["roles"] == ["Instructor"]


def test_multiple_roles_require_selection_and_issue_no_token(auth_env):
    ok, res = _login(auth_env, _user(["Receptionist", "Admin"]))

    assert ok is True
    assert res["role_selection_required"] is True
    assert res["roles"] == ["Admin", "Receptionist"]
    assert "token" not in res

    auth_env.jwt.encode.assert_not_called()
    auth_env.audit.assert_not_called()


def test_chosen_role_is_the_only_role_in_token(auth_env):
    ok, res = _login(auth_env, _user(["Receptionist", "Admin"]), role="Receptionist")

    assert ok is True
    assert res["role"] == "Receptionist"
    assert auth_env.jwt.encode.call_args.args[1]["roles"] == ["Receptionist"]
    assert auth_env.audit.call_args.kwargs["action"] == "LOGIN_SUCCESS"
    assert auth_env.audit.call_args.kwargs["new_value"] == {"role": "Receptionist"}


def test_role_the_user_does_not_have_is_rejected(auth_env):
    ok, message = _login(auth_env, _user(["Instructor"]), role="Admin")

    assert ok is False
    assert "szerepkör" in message
    auth_env.jwt.encode.assert_not_called()
    assert auth_env.audit.call_args.kwargs["new_value"]["reason"] == "invalid_role"


def test_wrong_password_does_not_reveal_roles(auth_env):
    ok, res = _login(auth_env, _user(["Admin", "Instructor"], password_ok=False))

    assert ok is False
    assert isinstance(res, str)
    auth_env.jwt.encode.assert_not_called()


@pytest.fixture
def verify_token():
    session = MagicMock()
    jwt = MagicMock()
    token_auth = MagicMock()
    token_auth.verify_token = lambda fn: fn

    dependencies = {
        "app": ModuleType("app"),
        "app.extensions": ModuleType("app.extensions"),
        "app.models": ModuleType("app.models"),
        "app.models.user": ModuleType("app.models.user"),
        "apiflask": ModuleType("apiflask"),
        "authlib": ModuleType("authlib"),
        "authlib.jose": ModuleType("authlib.jose"),
        "sqlalchemy": ModuleType("sqlalchemy"),
    }
    dependencies["apiflask"].APIBlueprint = MagicMock()
    dependencies["apiflask"].HTTPError = Exception
    dependencies["app.extensions"].auth = token_auth
    dependencies["app.extensions"].db = SimpleNamespace(session=session)
    dependencies["app.models.user"].User = object
    dependencies["authlib.jose"].jwt = jwt
    dependencies["sqlalchemy"].text = str

    app = Flask("verify-tests")
    app.config["PRIVATE_KEY"] = b"key"

    with app.app_context():
        module = _load(
            "blueprint_init_under_test",
            APP_DIR / "blueprints/__init__.py",
            dependencies,
        )
        yield module.verify_token, jwt, session


def _claims(roles):
    claims = {
        "user_id": 7,
        "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
    }
    if roles is not None:
        claims["roles"] = roles
    return claims


def test_token_only_grants_the_selected_role(verify_token):
    verify, jwt, session = verify_token
    jwt.decode.return_value = _claims(["Receptionist"])
    session.get.return_value = _user(["Receptionist", "Admin"])

    assert verify("t")["roles"] == ["Receptionist"]


def test_token_cannot_claim_a_role_the_user_lost(verify_token):
    verify, jwt, session = verify_token
    jwt.decode.return_value = _claims(["Admin"])
    session.get.return_value = _user(["Instructor"])

    assert verify("t")["roles"] == []


def test_token_without_roles_claim_falls_back_to_database_roles(verify_token):
    verify, jwt, session = verify_token
    jwt.decode.return_value = _claims(None)
    session.get.return_value = _user(["Instructor", "Admin"])

    assert verify("t")["roles"] == ["Instructor", "Admin"]
