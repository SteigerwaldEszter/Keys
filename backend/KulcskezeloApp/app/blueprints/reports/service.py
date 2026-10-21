import json
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
    return AuditLog.query.order_by(AuditLog.timestamp.desc()).all()

    def create_audit_log(
    action,
    entity_name,
    entity_value=None,
    user_id=None,
    old_value=None,
    new_value=None
):
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_name=entity_name,
        entity_value=(
            str(entity_value)
            if entity_value is not None
            else None
        ),
        old_value=(
            json.dumps(old_value, default=str, ensure_ascii=False)
            if old_value is not None
            else None
        ),
        new_value=(
            json.dumps(new_value, default=str, ensure_ascii=False)
            if new_value is not None
            else None
        )
    )

    db.session.add(audit_entry)
    return audit_entry


def get_audit_logs():
    return (
        AuditLog.query
        .order_by(
            AuditLog.timestamp.desc(),
            AuditLog.id.desc()
        )
        .all()
    )