from apiflask import APIBlueprint, HTTPError

from app.blueprints import role_required
from app.extensions import auth

from .schemas import (
    IssueCreateSchema,
    IssueOutSchema,
    IssueUpdateSchema,
)
from .service import (
    ALLOWED_ISSUE_STATUSES,
    create_issue,
    get_all_issues,
    update_issue_status,
)

bp = APIBlueprint("issues", __name__, url_prefix="/api/issues")


@bp.get("")
@bp.output(IssueOutSchema(many=True))
@bp.auth_required(auth)
def list_issues():
    return get_all_issues()


@bp.post("")
@bp.input(IssueCreateSchema)
@bp.output(IssueOutSchema, status_code=201)
@bp.auth_required(auth)
@role_required(["Receptionist", "Admin"])
def add_issue(json_data):
    if not json_data["title"].strip():
        raise HTTPError(
            400,
            message="A hibajegy címe nem lehet üres.",
        )

    return create_issue(
        issue_data=json_data,
        user_id=auth.current_user["user_id"],
    )


@bp.put("/<int:issue_id>")
@bp.input(IssueUpdateSchema)
@bp.output(IssueOutSchema)
@bp.auth_required(auth)
@role_required(["Receptionist", "Admin"])
def update_issue(issue_id, json_data):
    new_status = json_data["status"]

    if new_status not in ALLOWED_ISSUE_STATUSES:
        raise HTTPError(
            400,
            message="Érvénytelen hibajegystátusz.",
        )

    return update_issue_status(
        issue_id=issue_id,
        new_status=new_status,
        user_id=auth.current_user["user_id"],
    )
