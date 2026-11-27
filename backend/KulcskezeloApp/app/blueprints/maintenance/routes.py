from apiflask import APIBlueprint, HTTPError

from app.blueprints import role_required
from app.blueprints.maintenance.schemas import (
    ConflictingReservationSchema,
    MaintenanceCreateRequestSchema,
    MaintenanceListResponseSchema,
    MaintenanceWindowSchema,
    ReservationUpdateRequestSchema,
)
from app.blueprints.maintenance.service import MaintenanceService
from app.extensions import auth

bp = APIBlueprint("maintenance", __name__, tag="maintenance")


def validate_room_id(json_data):
    if not json_data["room_id"].strip():
        raise HTTPError(
            400,
            message="A teremazonosító nem lehet üres.",
        )


@bp.get("/list")
@bp.auth_required(auth)
@role_required("Admin")
@bp.output(MaintenanceListResponseSchema)
def list_maintenance_windows():
    return MaintenanceService.list_windows()


@bp.post("/create")
@bp.auth_required(auth)
@role_required("Admin")
@bp.input(MaintenanceCreateRequestSchema)
@bp.output(MaintenanceWindowSchema, status_code=201)
def create_maintenance_window(json_data):
    validate_room_id(json_data)

    return MaintenanceService.create_window(
        json_data,
        actor_user_id=auth.current_user["user_id"],
    )


@bp.put("/reservation/<int:id>")
@bp.auth_required(auth)
@role_required("Admin")
@bp.input(ReservationUpdateRequestSchema)
@bp.output(ConflictingReservationSchema)
def update_conflicting_reservation(id, json_data):
    validate_room_id(json_data)

    return MaintenanceService.update_conflicting_reservation(
        id,
        json_data,
        actor_user_id=auth.current_user["user_id"],
    )


@bp.delete("/delete/<int:id>")
@bp.auth_required(auth)
@role_required("Admin")
@bp.output({}, status_code=204)
def delete_maintenance_window(id):
    MaintenanceService.delete_window(
        id,
        actor_user_id=auth.current_user["user_id"],
    )
    return ""
