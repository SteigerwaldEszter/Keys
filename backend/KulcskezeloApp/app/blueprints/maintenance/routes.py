from apiflask import APIBlueprint

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


@bp.get("/list")
@bp.auth_required(auth)
@role_required("Admin")
@bp.output(MaintenanceListResponseSchema)
def list_maintenance_windows():
    """Karbantartási idősávok listája az ütköző foglalásokkal együtt."""
    return MaintenanceService.list_windows()


@bp.post("/create")
@bp.auth_required(auth)
@role_required("Admin")
@bp.input(MaintenanceCreateRequestSchema)
@bp.output(MaintenanceWindowSchema, status_code=201)
def create_maintenance_window(json_data):
    """Karbantartási idősáv létrehozása."""
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
    """Ütköző foglalás áthelyezése másik terembe vagy időpontra."""
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
    """Karbantartási idősáv törlése."""
    MaintenanceService.delete_window(
        id,
        actor_user_id=auth.current_user["user_id"],
    )

    return ""
