from app.blueprints.reports.service import create_audit_log
from app.extensions import db
from app.models.room_tool import RoomTool
from app.models.tool import Tool


class ToolService:
    @staticmethod
    def get_all_tools():
        try:
            tools = Tool.query.all()
            return True, {"tools": tools}

        except Exception:
            return False, "Hiba az eszközök lekérdezésekor."

    @staticmethod
    def create_tool(data, actor_user_id):
        try:
            name = data["name"].strip()

            if not name:
                return False, "Az eszköz neve nem lehet üres."

            tool = Tool(name=name)

            db.session.add(tool)
            db.session.flush()

            create_audit_log(
                action="TOOL_CREATED",
                entity_name="tools",
                entity_value=tool.id,
                user_id=actor_user_id,
                new_value={
                    "id": tool.id,
                    "name": tool.name,
                },
            )

            db.session.commit()
            return True, tool

        except Exception:
            db.session.rollback()
            return False, "Hiba az eszköz létrehozásakor."

    @staticmethod
    def delete_tool(tool_id, actor_user_id):
        try:
            tool = db.session.get(Tool, tool_id)

            if not tool:
                return False, "Eszköz nem található."

            linked_room = RoomTool.query.filter_by(tool_id=tool_id).first()

            if linked_room:
                return (
                    False,
                    "Az eszköz nem törölhető, mert teremhez van rendelve.",
                )

            old_data = {
                "id": tool.id,
                "name": tool.name,
            }

            create_audit_log(
                action="TOOL_DELETED",
                entity_name="tools",
                entity_value=tool.id,
                user_id=actor_user_id,
                old_value=old_data,
            )

            db.session.delete(tool)
            db.session.commit()

            return True, None

        except Exception:
            db.session.rollback()
            return False, "Hiba az eszköz törlésekor."

    @staticmethod
    def get_tool_by_id(tool_id):
        try:
            tool = db.session.get(Tool, tool_id)

            if not tool:
                return False, "Eszköz nem található."

            return True, tool

        except Exception:
            return False, "Hiba az eszköz lekérdezésekor."
