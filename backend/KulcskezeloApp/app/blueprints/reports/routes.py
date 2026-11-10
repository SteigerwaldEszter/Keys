from apiflask import APIBlueprint, HTTPError
from flask import current_app, request

from app.blueprints import role_required
from app.extensions import auth

from .schemas import AuditLogOutSchema, MissingKeySchema, UsageReportSchema
from .service import get_audit_logs, get_missing_keys, get_usage_statistics

bp = APIBlueprint("reports", __name__, url_prefix="/api")


@bp.get("/reports/usage")
@bp.output(UsageReportSchema)
@bp.auth_required(auth)
@role_required("Director")
def usage_report():
    return get_usage_statistics()


@bp.get("/reports/missing-keys")
@bp.output(MissingKeySchema(many=True))
@bp.auth_required(auth)
@role_required("Director")
def missing_keys_report():
    return get_missing_keys()


@bp.get("/audit-logs")
@bp.output(AuditLogOutSchema(many=True))
@bp.auth_required(auth)
@role_required("Director")
def audit_logs():
    raw_limit = request.args.get("limit")

    if raw_limit is not None:
        try:
            limit = int(raw_limit)
        except ValueError:
            raise HTTPError(
                400,
                message="A limit paraméternek egész számnak kell lennie.",
            ) from None

        if not 1 <= limit <= 1000:
            raise HTTPError(
                400,
                message="A limit értékének 1 és 1000 között kell lennie.",
            )
    else:
        limit = None

    try:
        logs = get_audit_logs()
    except Exception:
        current_app.logger.exception("Hiba az audit logok lekérdezésekor.")
        raise HTTPError(
            500,
            message="Szerverhiba történt az audit logok lekérdezésekor.",
        ) from None

    if limit is not None:
        return logs[:limit]

    return logs
