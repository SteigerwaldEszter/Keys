from apiflask import APIBlueprint, HTTPError

from app.blueprints import role_required
from app.blueprints.classrooms.schemas import (
    ClassroomCreateRequestSchema,
    ClassroomDetailResponseSchema,
    ClassroomFilterSchema,
    ClassroomListResponseSchema,
    ClassroomUpdateRequestSchema,
)
from app.blueprints.classrooms.service import ClassroomService
from app.extensions import auth

bp = APIBlueprint("classrooms", __name__, tag="classrooms")


@bp.route("/")
def index():
    return "This is The Classrooms Blueprint"


@bp.get("/list")
@bp.auth_required(auth)
@bp.input(ClassroomFilterSchema, location="query")
@bp.output(ClassroomListResponseSchema)
def get_classrooms(query_data):
    success, res = ClassroomService.get_filtered_classrooms(query_data)

    if success:
        return res
    raise HTTPError(400, res)


@bp.get("/list")
@bp.auth_required(auth)
@role_required("Admin")
@bp.output(ClassroomListResponseSchema)
def get_all_classrooms(query_data):
    success, res = ClassroomService.get_filtered_classrooms(query_data)

    if success:
        return res
    raise HTTPError(400, res)


@bp.get("/<string:id>")
@bp.auth_required(auth)
@bp.output(ClassroomDetailResponseSchema)
def get_classroom_by_id(id):
    success, res = ClassroomService.get_classroom_by_id(id)
    if success:
        return res
    raise HTTPError(404, res)


@bp.post("/create")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.input(ClassroomCreateRequestSchema)
@bp.output(ClassroomDetailResponseSchema, status_code=201)
def create_classroom(json_data):
    """Új terem és teremtörzs adatok felvitele."""
    success, res = ClassroomService.create_classroom(json_data)
    if success:
        return res
    raise HTTPError(400, res)


@bp.put("/update/<string:id>")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.input(ClassroomUpdateRequestSchema)
@bp.output(ClassroomDetailResponseSchema)
def update_classroom(id, json_data):
    """Terem adatainak frissítése."""
    success, res = ClassroomService.update_classroom(id, json_data)
    if success:
        return res
    raise HTTPError(400, res)


@bp.delete("/<string:id>")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.output({}, status_code=204)
def delete_classroom(id):
    """Terem törlése (vagy inaktívvá tétele)."""
    success, res = ClassroomService.delete_classroom(id)
    if success:
        return ""
    raise HTTPError(400, res)
