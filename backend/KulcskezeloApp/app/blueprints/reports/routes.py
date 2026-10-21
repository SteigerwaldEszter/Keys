from apiflask import APIBlueprint

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
    return get_audit_logs()
