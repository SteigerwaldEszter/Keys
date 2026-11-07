from apiflask import APIBlueprint, HTTPError

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
    succes, res = get_usage_statistics()
    if succes:
        return res
    raise HTTPError(400, res)


@bp.get("/reports/missing-keys")
@bp.output(MissingKeySchema(many=True))
@bp.auth_required(auth)
@role_required("Director")
def missing_keys_report():
    succes, res = get_missing_keys()
    if succes:
        return res
    raise HTTPError(400, res)


@bp.get("/audit-logs")
@bp.output(AuditLogOutSchema(many=True))
@bp.auth_required(auth)
@role_required("Director")
def audit_logs():
    succes, res = get_audit_logs()
    if succes:
        return res
    raise HTTPError(400, res)