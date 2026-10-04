from apiflask import APIBlueprint, HTTPError

from app.blueprints import role_required
from app.blueprints.reservations.schemas import (
    ReservationCreateRequestSchema,
    ReservationListResponseSchema,
    ReservationSchema,
    ReservationStatusUpdateRequestSchema,
)
from app.blueprints.reservations.service import ReservationService
from app.extensions import auth

bp = APIBlueprint("reservations", __name__, tag="reservations")


@bp.route("/")
def index():
    return "This is The Reservations Blueprint"


@bp.get("/list")
@bp.auth_required(auth)
@bp.output(ReservationListResponseSchema)
def get_reservations():
    """Foglalások listázása a felhasználó szerepköre alapján."""
    current_user = auth.current_user

    success, res = ReservationService.get_reservations(current_user)
    if success:
        return res
    raise HTTPError(400, res)


@bp.post("/create")
@bp.auth_required(auth)
@role_required(["Instructor", "Admin"])
@bp.input(ReservationCreateRequestSchema)
@bp.output(ReservationSchema, status_code=201)
def create_reservation(json_data):

    current_user = auth.current_user

    success, res = ReservationService.create_reservation(current_user, json_data)
    if success:
        return res
    raise HTTPError(400, res)


@bp.put("/status/<int:id>")
@bp.auth_required(auth)
@role_required(["Receptionist", "Admin"])
@bp.input(ReservationStatusUpdateRequestSchema)
@bp.output(ReservationSchema)
def update_reservation_status(id, json_data):
    """Foglalás állapotának frissítése (pl. lemondás, no-show)."""
    current_user = auth.current_user

    success, res = ReservationService.update_status(
        id, json_data["status"], current_user
    )
    if success:
        return res
    raise HTTPError(400, res)


@bp.delete("/delete/<int:id>")
@bp.auth_required(auth)
@role_required(["Instructor", "Admin"])
def delete_reservation(id):
    """Foglalás törlése."""
    current_user = auth.current_user

    success, res = ReservationService.delete_reservation(id, current_user)
    if success:
        return "", 204
    raise HTTPError(400, res)
