from apiflask import abort

from app.blueprints.reports.service import create_audit_log
from app.extensions import db
from app.models.classroom import Classroom
from app.models.issue_ticket import IssueTicket

ALLOWED_ISSUE_STATUSES = {
    "open",
    "in_progress",
    "resolved",
    "closed",
}


def get_all_issues():
    return IssueTicket.query.all()


def create_issue(issue_data: dict, user_id: int):
    room = db.session.get(Classroom, issue_data["room_id"])

    if room is None:
        abort(404, message="A megadott terem nem található.")

    title = issue_data["title"].strip()

    if not title:
        abort(400, message="A hibajegy címe nem lehet üres.")

    try:
        issue = IssueTicket(
            room_id=room.id,
            user_id=user_id,
            title=title,
            description=issue_data.get("description", ""),
            status="open",
        )

        db.session.add(issue)
        db.session.flush()

        create_audit_log(
            action="ISSUE_CREATED",
            entity_name="issue_tickets",
            entity_value=issue.id,
            user_id=user_id,
            new_value={
                "room_id": issue.room_id,
                "reported_by": issue.user_id,
                "title": issue.title,
                "description": issue.description,
                "status": issue.status,
            },
        )

        db.session.commit()
        return issue

    except Exception:
        db.session.rollback()
        raise


def update_issue_status(
    issue_id: int,
    new_status: str,
    user_id: int,
):
    if new_status not in ALLOWED_ISSUE_STATUSES:
        abort(400, message="Érvénytelen hibajegystátusz.")

    issue = IssueTicket.query.get_or_404(issue_id)

    old_status = issue.status

    if old_status == new_status:
        return issue

    try:
        issue.status = new_status

        create_audit_log(
            action="ISSUE_UPDATED",
            entity_name="issue_tickets",
            entity_value=issue.id,
            user_id=user_id,
            old_value={
                "status": old_status,
            },
            new_value={
                "status": new_status,
            },
        )

        db.session.commit()
        return issue

    except Exception:
        db.session.rollback()
        raise
