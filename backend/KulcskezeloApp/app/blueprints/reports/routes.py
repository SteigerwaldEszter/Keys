from apiflask import APIBlueprint

from .schemas import AuditLogOutSchema, MissingKeySchema, UsageReportSchema
from .service import get_audit_logs, get_missing_keys, get_usage_statistics

bp = APIBlueprint("reports", __name__, url_prefix="/api")


@bp.get("/reports/usage")
@bp.output(UsageReportSchema)
def usage_report():
    # Napi és heti teremkihasználtsági, illetve forgalmi statisztikák generálása
    return get_usage_statistics()


@bp.get("/reports/missing-keys")
@bp.output(MissingKeySchema(many=True))
def missing_keys_report():
    # Elmaradt (határidőn túli) kulcsleadások lekérése automatikus jelzés céljából
    return get_missing_keys()


@bp.get("/audit-logs")
@bp.output(AuditLogOutSchema(many=True))
def audit_logs():
    # Részletes biztonsági eseménynapló lekérése a rendszer összes módosításáról
    return get_audit_logs()
