import json
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from sys import modules
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "KulcskezeloApp"
    / "app"
    / "blueprints"
    / "reports"
    / "service.py"
)


@pytest.fixture
def setup_audit():
    class AuditLog:
        def __init__(self, **values):
            self.__dict__.update(values)

    session = MagicMock()
    dependencies = {
        name: ModuleType(name)
        for name in (
            "app",
            "app.blueprints",
            "app.blueprints.reports",
            "app.extensions",
            "app.models",
            "app.models.audit_log",
            "app.models.key",
            "app.models.key_log",
            "app.models.reservation",
        )
    }
    dependencies["app.extensions"].db = SimpleNamespace(session=session)
    dependencies["app.models.audit_log"].AuditLog = AuditLog
    dependencies["app.models.key"].Key = type("Key", (), {})
    dependencies["app.models.key_log"].KeyLog = type("KeyLog", (), {})
    dependencies["app.models.reservation"].Reservation = type("Reservation", (), {})

    with patch.dict(modules, dependencies):
        spec = spec_from_file_location("audit_service_under_test", SOURCE)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module, session


def test_audit_log_saves_action_and_actor(setup_audit):
    module, session = setup_audit

    entry = module.create_audit_log("KEY_CHECKOUT", "keys", entity_value=12, user_id=4)

    assert entry.action == "KEY_CHECKOUT"
    assert entry.entity_name == "keys"
    assert entry.entity_value == "12"
    assert entry.user_id == 4
    session.add.assert_called_once_with(entry)
    session.commit.assert_not_called()


def test_audit_log_serializes_old_and_new_values(setup_audit):
    module, _ = setup_audit

    entry = module.create_audit_log(
        "KEY_RETURN",
        "keys",
        entity_value=1,
        old_value={"status": "handed_out"},
        new_value={"status": "available"},
    )

    assert json.loads(entry.old_value) == {"status": "handed_out"}
    assert json.loads(entry.new_value) == {"status": "available"}


def test_audit_log_accepts_empty_values(setup_audit):
    module, _ = setup_audit

    entry = module.create_audit_log("LOGIN_FAILED", "authentication")

    assert entry.entity_value is None
    assert entry.old_value is None
    assert entry.new_value is None


def test_audit_log_can_serialize_datetime(setup_audit):
    module, _ = setup_audit
    timestamp = datetime(2026, 11, 2, 10, 45)

    entry = module.create_audit_log(
        "BOOKING_CREATED", "reservations", new_value={"end_time": timestamp}
    )

    assert json.loads(entry.new_value)["end_time"] == "2026-11-02 10:45:00"
