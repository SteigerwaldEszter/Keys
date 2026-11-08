from datetime import datetime, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from sys import modules
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "KulcskezeloApp"
    / "app"
    / "blueprints"
    / "keys"
    / "deadlines.py"
)

NOW = datetime(2026, 11, 9, 12, 0)


class Column:
    def __eq__(self, other):
        return True

    def __lt__(self, other):
        return True

    def __invert__(self):
        return True

    def in_(self, values):
        return True

    def desc(self):
        return True

    def any(self, *args):
        return True


@pytest.fixture
def setup_deadlines():
    class Reservation:
        status = Column()
        start_time = Column()
        key_logs = Column()
        query = MagicMock()

    class KeyLog:
        id = Column()
        action = Column()
        query = MagicMock()

    class Key:
        query = MagicMock()

    class AuditLog:
        query = MagicMock()

    session = MagicMock()
    audit = MagicMock()

    dependencies = {
        "app": ModuleType("app"),
        "app.blueprints": ModuleType("app.blueprints"),
        "app.blueprints.reports": ModuleType("app.blueprints.reports"),
        "app.blueprints.reports.service": ModuleType("app.blueprints.reports.service"),
        "app.extensions": ModuleType("app.extensions"),
        "app.models": ModuleType("app.models"),
        "app.models.audit_log": ModuleType("app.models.audit_log"),
        "app.models.key": ModuleType("app.models.key"),
        "app.models.key_log": ModuleType("app.models.key_log"),
        "app.models.reservation": ModuleType("app.models.reservation"),
    }

    dependencies["app.blueprints.reports.service"].create_audit_log = audit
    dependencies["app.extensions"].db = SimpleNamespace(session=session)
    dependencies["app.models.audit_log"].AuditLog = AuditLog
    dependencies["app.models.key"].Key = Key
    dependencies["app.models.key_log"].KeyLog = KeyLog
    dependencies["app.models.reservation"].Reservation = Reservation

    app = Flask("deadline-tests")

    with patch.dict(modules, dependencies), app.app_context():
        spec = spec_from_file_location("deadlines_under_test", SOURCE)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        yield SimpleNamespace(
            module=module,
            Reservation=Reservation,
            KeyLog=KeyLog,
            Key=Key,
            AuditLog=AuditLog,
            session=session,
            audit=audit,
            app=app,
        )


def _no_show_candidates(env, items):
    query = env.Reservation.query.filter.return_value
    query.with_for_update.return_value.all.return_value = items


def test_unpicked_reservation_becomes_no_show(setup_deadlines):
    env = setup_deadlines
    reservation = SimpleNamespace(id=5, status="active")
    _no_show_candidates(env, [reservation])

    changed = env.module.mark_no_shows(NOW)

    assert changed == [5]
    assert reservation.status == "no-show"

    kwargs = env.audit.call_args.kwargs
    assert kwargs["action"] == "BOOKING_NO_SHOW"
    assert kwargs["user_id"] is None
    assert kwargs["old_value"] == {"status": "active"}
    assert kwargs["new_value"]["status"] == "no-show"
    assert kwargs["new_value"]["automatic"] is True

    env.session.commit.assert_called_once()


def test_no_show_does_nothing_without_candidates(setup_deadlines):
    env = setup_deadlines
    _no_show_candidates(env, [])

    assert env.module.mark_no_shows(NOW) == []

    env.audit.assert_not_called()


def test_no_show_rolls_back_on_error(setup_deadlines):
    env = setup_deadlines
    _no_show_candidates(env, [SimpleNamespace(id=1, status="pending")])
    env.audit.side_effect = RuntimeError("db down")

    with pytest.raises(RuntimeError):
        env.module.mark_no_shows(NOW)

    env.session.rollback.assert_called_once()
    env.session.commit.assert_not_called()


def _handed_out_key(env, end_time, key_id=3):
    key = SimpleNamespace(id=key_id, name="Kulcs", room_id="I1", is_master=False)
    issue = SimpleNamespace(id=40, reservation_id=9, receiver_id=2)
    env.Key.query.filter_by.return_value.all.return_value = [key]
    env.KeyLog.query.filter_by.return_value.order_by.return_value.first.return_value = (
        issue
    )
    env.session.get.return_value = SimpleNamespace(id=9, end_time=end_time)


def test_key_within_grace_is_not_overdue(setup_deadlines):
    env = setup_deadlines
    _handed_out_key(env, NOW - timedelta(minutes=10))

    assert env.module.get_overdue_keys(NOW) == []


def test_key_after_grace_is_overdue(setup_deadlines):
    env = setup_deadlines
    _handed_out_key(env, NOW - timedelta(minutes=45))

    items = env.module.get_overdue_keys(NOW)

    assert len(items) == 1
    assert items[0]["key_id"] == 3
    assert items[0]["reservation_id"] == 9
    assert items[0]["minutes_late"] == 45


def test_grace_comes_from_config(setup_deadlines):
    env = setup_deadlines
    env.app.config["LATE_RETURN_GRACE_MINUTES"] = 60
    _handed_out_key(env, NOW - timedelta(minutes=45))

    assert env.module.get_overdue_keys(NOW) == []


def test_overdue_key_is_logged_once(setup_deadlines):
    env = setup_deadlines
    _handed_out_key(env, NOW - timedelta(minutes=45))

    env.AuditLog.query.filter_by.return_value.first.return_value = None
    assert env.module.flag_overdue_keys(NOW) == [40]
    assert env.audit.call_args.kwargs["action"] == "KEY_RETURN_OVERDUE"
    assert env.audit.call_args.kwargs["entity_value"] == 40

    env.audit.reset_mock()
    env.AuditLog.query.filter_by.return_value.first.return_value = object()
    assert env.module.flag_overdue_keys(NOW) == []
    env.audit.assert_not_called()


def test_key_without_issue_log_is_ignored(setup_deadlines):
    env = setup_deadlines
    env.Key.query.filter_by.return_value.all.return_value = [SimpleNamespace(id=1)]
    env.KeyLog.query.filter_by.return_value.order_by.return_value.first.return_value = (
        None
    )

    assert env.module.get_overdue_keys(NOW) == []
