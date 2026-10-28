from datetime import datetime, timedelta
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
    / "reservations"
    / "service.py"
)


class Column:
    def __eq__(self, other):
        return True

    def __lt__(self, other):
        return True

    def __gt__(self, other):
        return True

    def in_(self, values):
        return True


@pytest.fixture
def setup_service():
    class Reservation:
        room_id = Column()
        status = Column()
        start_time = Column()
        end_time = Column()
        query = MagicMock()
        next_id = 1

        def __init__(self, **values):
            self.__dict__.update(values)
            self.id = Reservation.next_id
            Reservation.next_id += 1

    session = MagicMock()
    audit = MagicMock()

    dependencies = {
        "app": ModuleType("app"),
        "app.blueprints": ModuleType("app.blueprints"),
        "app.blueprints.reports": ModuleType("app.blueprints.reports"),
        "app.blueprints.reports.service": ModuleType("app.blueprints.reports.service"),
        "app.extensions": ModuleType("app.extensions"),
        "app.models": ModuleType("app.models"),
        "app.models.reservation": ModuleType("app.models.reservation"),
    }
    dependencies["app.extensions"].db = SimpleNamespace(session=session)
    dependencies["app.models.reservation"].Reservation = Reservation
    dependencies["app.blueprints.reports.service"].create_audit_log = audit

    with patch.dict(modules, dependencies):
        spec = spec_from_file_location("reservation_service_under_test", SOURCE)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module.ReservationService, Reservation, session, audit


@pytest.mark.parametrize("slots", [0, 7])
def test_rejects_invalid_duration(setup_service, slots):
    service, _, session, audit = setup_service
    success, message = service.create_reservation(
        {"user_id": 2},
        {
            "room_id": "I1",
            "start_time": datetime(2026, 11, 2, 10),
            "duration_slots": slots,
        },
    )
    assert success is False
    assert "blokkok" in message
    session.commit.assert_not_called()
    audit.assert_not_called()


@pytest.mark.parametrize("weeks", [0, 16])
def test_rejects_invalid_recurring_weeks(setup_service, weeks):
    service, _, session, audit = setup_service
    success, message = service.create_reservation(
        {"user_id": 2},
        {
            "room_id": "I1",
            "start_time": datetime(2026, 11, 2, 10),
            "recurring_weeks": weeks,
        },
    )
    assert success is False
    assert "ismétlődések" in message
    session.commit.assert_not_called()
    audit.assert_not_called()


def test_recurring_reservations_create_audit_entries(setup_service):
    service, reservation, session, audit = setup_service
    reservation.query.filter.return_value.first.return_value = None
    start = datetime(2026, 11, 2, 10)

    success, result = service.create_reservation(
        {"user_id": 2},
        {
            "room_id": "I1",
            "start_time": start,
            "duration_slots": 2,
            "recurring_weeks": 2,
        },
    )

    assert success is True
    assert "2 db" in result["message"]
    created = session.add_all.call_args.args[0]
    assert len(created) == 2
    assert created[0].end_time == start + timedelta(minutes=90)
    assert created[1].start_time == start + timedelta(weeks=1)
    assert audit.call_count == 2
    assert audit.call_args_list[0].kwargs["action"] == "BOOKING_CREATED"
    assert audit.call_args_list[1].kwargs["new_value"]["user_id"] == 2
    session.commit.assert_called_once()


def test_conflicting_reservation_is_rejected(setup_service):
    service, reservation, session, audit = setup_service
    reservation.query.filter.return_value.first.return_value = object()

    success, message = service.create_reservation(
        {"user_id": 2}, {"room_id": "I1", "start_time": datetime(2026, 11, 2, 10)}
    )

    assert success is False
    assert "Ütközés" in message
    session.add_all.assert_not_called()
    audit.assert_not_called()


def test_instructor_can_only_list_own_reservations(setup_service):
    service, reservation, _, _ = setup_service
    reservation.query.filter_by.return_value.all.return_value = ["own"]

    success, result = service.get_reservations({"user_id": 2, "roles": ["Instructor"]})

    assert success is True
    assert result["reservations"] == ["own"]
    reservation.query.filter_by.assert_called_once_with(user_id=2)
    reservation.query.all.assert_not_called()


def test_director_can_list_all_reservations(setup_service):
    service, reservation, _, _ = setup_service
    reservation.query.all.return_value = ["first", "second"]

    success, result = service.get_reservations({"user_id": 3, "roles": ["Director"]})

    assert success is True
    assert len(result["reservations"]) == 2
    reservation.query.all.assert_called_once()


def test_invalid_status_is_not_saved(setup_service):
    service, reservation, session, audit = setup_service
    reservation.query.get.return_value = SimpleNamespace(status="active")

    success, message = service.update_status(1, "nonsense", {"user_id": 4})

    assert success is False
    assert "státusz" in message
    session.commit.assert_not_called()
    audit.assert_not_called()


def test_status_change_records_old_and_new_values(setup_service):
    service, reservation, session, audit = setup_service
    item = SimpleNamespace(id=1, status="active")
    reservation.query.get.return_value = item

    success, updated = service.update_status(1, "no-show", {"user_id": 4})

    assert success is True
    assert updated.status == "no-show"
    assert audit.call_args.kwargs["action"] == "BOOKING_NO_SHOW"
    assert audit.call_args.kwargs["old_value"] == {"status": "active"}
    assert audit.call_args.kwargs["new_value"] == {"status": "no-show"}
    session.commit.assert_called_once()


def test_unchanged_status_does_not_create_extra_audit_log(setup_service):
    service, reservation, session, audit = setup_service
    reservation.query.get.return_value = SimpleNamespace(id=1, status="active")

    success, _ = service.update_status(1, "active", {"user_id": 4})

    assert success is True
    audit.assert_not_called()
    session.commit.assert_not_called()


def test_instructor_cannot_delete_another_users_reservation(setup_service):
    service, reservation, session, audit = setup_service
    reservation.query.get.return_value = SimpleNamespace(id=1, user_id=7)

    success, message = service.delete_reservation(
        1, {"user_id": 2, "roles": ["Instructor"]}
    )

    assert success is False
    assert "jogosultság" in message
    session.delete.assert_not_called()
    audit.assert_not_called()


def test_admin_deletion_is_audited(setup_service):
    service, reservation, session, audit = setup_service
    reservation.query.get.return_value = SimpleNamespace(
        id=1,
        user_id=7,
        room_id="I1",
        start_time=datetime(2026, 11, 2, 10),
        end_time=datetime(2026, 11, 2, 10, 45),
        status="active",
    )

    success, _ = service.delete_reservation(1, {"user_id": 1, "roles": ["Admin"]})

    assert success is True
    assert audit.call_args.kwargs["action"] == "BOOKING_DELETED"
    assert audit.call_args.kwargs["old_value"]["user_id"] == 7
    session.delete.assert_called_once()
    session.commit.assert_called_once()
