from apiflask import abort

from app.extensions import db
from app.models.classroom import Classroom
from app.models.issue_ticket import IssueTicket


def get_all_issues():
    return IssueTicket.query.all()


def create_issue(issue_data: dict, user_id: int):
    room = Classroom.query.get(issue_data["room_id"])
    if not room:
        abort(404, "A megadott terem (room_id) nem található az adatbázisban.")

    issue = IssueTicket(
        room_id=issue_data["room_id"],
        user_id=user_id,
        title=issue_data["title"],
        description=issue_data.get("description", ""),
    )
    db.session.add(issue)
    db.session.commit()
    return issue


def update_issue_status(issue_id: int, new_status: str):
    issue = IssueTicket.query.get_or_404(issue_id)
    issue.status = new_status
    db.session.commit()
    return issue
