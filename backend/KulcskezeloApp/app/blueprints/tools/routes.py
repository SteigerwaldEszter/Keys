from apiflask import APIBlueprint, HTTPError

from app.blueprints import role_required
from app.blueprints.tools.schemas import (
    ToolCreateRequestSchema,
    ToolListResponseSchema,
    ToolSchema,
)
from app.blueprints.tools.service import ToolService
from app.extensions import auth

bp = APIBlueprint("tools", __name__, tag="tools")


@bp.route("/")
def index():
    return "This is The Tools Blueprint"


@bp.get("/list")
@bp.auth_required(auth)
@bp.output(ToolListResponseSchema)
def get_tools():
    """A rendszerben nyilvántartott speciális technikai eszközök listázása."""
    success, res = ToolService.get_all_tools()
    if success:
        return res
    raise HTTPError(400, res)


@bp.post("/create")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.input(ToolCreateRequestSchema)
@bp.output(ToolSchema)
def create_tool(json_data):
    success, res = ToolService.create_tool(json_data)
    if success:
        return res
    raise HTTPError(400, res)


@bp.delete("/delete/<int:id>")
@bp.auth_required(auth)
@role_required(["Admin"])
@bp.output({}, status_code=204)
def delete_tool(id):
    """Eszköz törlése"""
    success, res = ToolService.delete_tool(id)
    if success:
        return ""
    raise HTTPError(400, res)


@bp.get("/<int:id>")
@bp.auth_required(auth)
@bp.output(ToolSchema)
def get_tool_by_id(id):
    success, res = ToolService.get_tool_by_id(id)
    if success:
        return res
    raise HTTPError(404, res)
