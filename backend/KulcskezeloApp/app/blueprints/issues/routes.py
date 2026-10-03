from apiflask import APIBlueprint

from app.extensions import auth

from .schemas import IssueCreateSchema, IssueOutSchema, IssueUpdateSchema
from .service import create_issue, get_all_issues, update_issue_status

bp = APIBlueprint("issues", __name__, url_prefix="/api/issues")


@bp.get("")
@bp.output(IssueOutSchema(many=True))
def list_issues():
    # Hibajegyek listázása
    return get_all_issues()


@bp.post("")
@bp.input(IssueCreateSchema)
@bp.output(IssueOutSchema, status_code=201)
@bp.auth_required(auth)
def add_issue(data):
    # Új hibajegy felvétele meghibásodás vagy rendellenesség esetén
    current_user_id = auth.current_user["user_id"]
    return create_issue(data, user_id=current_user_id)


@bp.put("/<int:issue_id>")
@bp.input(IssueUpdateSchema)
@bp.output(IssueOutSchema)
def update_issue(issue_id, data):
    # Hibajegy állapotának (pl. nyitott/megoldva) frissítése
    return update_issue_status(issue_id, data["status"])
