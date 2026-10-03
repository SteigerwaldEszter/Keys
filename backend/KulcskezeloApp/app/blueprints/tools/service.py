from app.extensions import db
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
    def create_tool(data):
        try:
            tool = Tool(**data)
            db.session.add(tool)
            db.session.commit()
            return True, tool
        except Exception:
            db.session.rollback()
            return False, "Hiba az eszköz létrehozásakor."

    @staticmethod
    def delete_tool(tool_id):
        try:
            tool = Tool.query.get(tool_id)
            if not tool:
                return False, "Eszköz nem található."
            db.session.delete(tool)
            db.session.commit()
            return True, None
        except Exception:
            db.session.rollback()
            return False, "Hiba az eszköz törlésekor."

    @staticmethod
    def get_tool_by_id(tool_id):
        try:
            tool = Tool.query.get(tool_id)
            if not tool:
                return False, "Eszköz nem található."
            return True, tool
        except Exception:
            return False, "Hiba az eszköz lekérdezésekor."
