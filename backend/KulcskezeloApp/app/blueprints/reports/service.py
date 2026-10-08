from datetime import datetime

from flask import has_request_context
from sqlalchemy import event

from app.extensions import auth, db
from app.models.audit_log import AuditLog
from app.models.key import Key
from app.models.key_log import KeyLog
from app.models.reservation import Reservation


def get_usage_statistics():
    total = Key.query.count()
    handed_out = Key.query.filter_by(status="handed_out").count()
    available = Key.query.filter_by(status="available").count()

    return {
        "total_keys": total,
        "handed_out_keys": handed_out,
        "available_keys": available,
    }


def get_missing_keys():
    now = datetime.now()
    missing_keys_list = []

    handed_out_keys = Key.query.filter_by(status="handed_out").all()

    for key in handed_out_keys:
        last_issue_log = (
            KeyLog.query.filter_by(key_id=key.id, action="ISSUE")
            .order_by(KeyLog.id.desc())
            .first()
        )

        if last_issue_log and last_issue_log.reservation_id:
            reservation = Reservation.query.get(last_issue_log.reservation_id)
            if reservation and reservation.end_time < now:
                missing_keys_list.append(
                    {
                        "key_id": key.id,
                        "room_id": key.room_id,
                        "reservation_id": reservation.id,
                        "end_time": reservation.end_time,
                        "handler_id": last_issue_log.handler_id,
                    }
                )

    return missing_keys_list


def get_audit_logs():
    return AuditLog.query.order_by(AuditLog.created_at.desc()).all()


def setup_audit_logging():
    def log_change(mapper, connection, target, action):
        if target.__tablename__ == "audit_logs":
            return

        current_user_id = None
        if (
            has_request_context()
            and hasattr(auth, "current_user")
            and auth.current_user
        ):
            current_user_id = auth.current_user.get("user_id")

        if current_user_id is None:
            return

        audit_entry = AuditLog(
            entity_name=target.__tablename__,
            entity_value=str(getattr(target, "id", "")),
            action=action,
            user_id=current_user_id,
        )
        db.session.add(audit_entry)

    event.listen(
        db.Model,
        "after_insert",
        lambda m, c, t: log_change(m, c, t, "INSERT"),
        propagate=True,
    )
    event.listen(
        db.Model,
        "after_update",
        lambda m, c, t: log_change(m, c, t, "UPDATE"),
        propagate=True,
    )
    event.listen(
        db.Model,
        "after_delete",
        lambda m, c, t: log_change(m, c, t, "DELETE"),
        propagate=True,
    )
