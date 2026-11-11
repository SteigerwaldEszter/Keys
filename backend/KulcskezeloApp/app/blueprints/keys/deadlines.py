from datetime import datetime, timedelta

from flask import current_app

from app.blueprints.reports.service import create_audit_log
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.key import Key
from app.models.key_log import KeyLog
from app.models.reservation import Reservation

OPEN_RESERVATION_STATUSES = ("pending", "active")


def _minutes(config_name, default):
    try:
        return int(current_app.config.get(config_name, default))
    except (TypeError, ValueError):
        return default


def no_show_grace():
    return timedelta(minutes=_minutes("NO_SHOW_GRACE_MINUTES", 15))


def late_return_grace():
    return timedelta(minutes=_minutes("LATE_RETURN_GRACE_MINUTES", 15))


def mark_no_shows(now=None):
    now = now or datetime.now()
    cutoff = now - no_show_grace()

    candidates = (
        Reservation.query.filter(
            Reservation.status.in_(OPEN_RESERVATION_STATUSES),
            Reservation.start_time < cutoff,
            ~Reservation.key_logs.any(KeyLog.action == "ISSUE"),
        )
        .with_for_update()
        .all()
    )

    changed = []

    try:
        for reservation in candidates:
            old_status = reservation.status
            reservation.status = "no-show"

            create_audit_log(
                action="BOOKING_NO_SHOW",
                entity_name="reservations",
                entity_value=reservation.id,
                user_id=None,
                old_value={"status": old_status},
                new_value={
                    "status": "no-show",
                    "reason": "key_not_picked_up",
                    "automatic": True,
                    "grace_minutes": int(no_show_grace().total_seconds() // 60),
                },
            )
            changed.append(reservation.id)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return changed


def mark_completed(now=None):

    now = now or datetime.now()

    candidates = (
        Reservation.query.filter(
            Reservation.status.in_(OPEN_RESERVATION_STATUSES),
            Reservation.end_time < now,
            Reservation.key_logs.any(KeyLog.action == "ISSUE"),
        )
        .with_for_update()
        .all()
    )

    changed = []

    try:
        for reservation in candidates:
            old_status = reservation.status
            reservation.status = "completed"

            create_audit_log(
                action="BOOKING_COMPLETED",
                entity_name="reservations",
                entity_value=reservation.id,
                user_id=None,
                old_value={"status": old_status},
                new_value={
                    "status": "completed",
                    "reason": "ended_after_key_issue",
                    "automatic": True,
                },
            )
            changed.append(reservation.id)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return changed


def get_overdue_keys(now=None):
    now = now or datetime.now()
    grace = late_return_grace()
    items = []

    for key in Key.query.filter_by(status="handed_out").all():
        issue = (
            KeyLog.query.filter_by(key_id=key.id, action="ISSUE")
            .order_by(KeyLog.id.desc())
            .first()
        )

        if issue is None:
            continue

        reservation = db.session.get(Reservation, issue.reservation_id)

        if reservation is None:
            continue

        due_at = reservation.end_time

        if now <= due_at + grace:
            continue

        items.append(
            {
                "key_id": key.id,
                "key_name": key.name,
                "room_id": key.room_id,
                "is_master": key.is_master,
                "reservation_id": reservation.id,
                "receiver_id": issue.receiver_id,
                "key_log_id": issue.id,
                "due_at": due_at,
                "minutes_late": int((now - due_at).total_seconds() // 60),
            }
        )

    return items


def flag_overdue_keys(now=None):
    now = now or datetime.now()
    items = get_overdue_keys(now)
    flagged = []

    try:
        for item in items:
            already = AuditLog.query.filter_by(
                action="KEY_RETURN_OVERDUE",
                entity_name="key_logs",
                entity_value=str(item["key_log_id"]),
            ).first()

            if already is not None:
                continue

            create_audit_log(
                action="KEY_RETURN_OVERDUE",
                entity_name="key_logs",
                entity_value=item["key_log_id"],
                user_id=None,
                new_value={
                    "key_id": item["key_id"],
                    "room_id": item["room_id"],
                    "reservation_id": item["reservation_id"],
                    "receiver_id": item["receiver_id"],
                    "due_at": item["due_at"],
                    "minutes_late": item["minutes_late"],
                    "automatic": True,
                },
            )
            flagged.append(item["key_log_id"])

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return flagged


def run_sweep(now=None):
    now = now or datetime.now()
    return {
        "no_show": mark_no_shows(now),
        "completed": mark_completed(now),
        "overdue": flag_overdue_keys(now),
    }
