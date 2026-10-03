from app.extensions import db
from app.models.classroom import Classroom
from app.models.reservation import Reservation
from app.models.room_tool import RoomTool
from app.models.tool import Tool
from app.models.type import Type


class ClassroomService:
    @staticmethod
    def get_filtered_classrooms(filters):
        try:
            query = Classroom.query.filter(Classroom.is_active == True)

            # Capacity filter
            capacity_min = filters.get("capacity_min")
            if capacity_min:
                query = query.filter(Classroom.capacity >= capacity_min)

            # Tools filter
            tools = filters.get("tools")
            if tools:
                for tool_name in tools:
                    has_tool_subquery = (
                        db.session.query(RoomTool.classroom_id)
                        .join(Tool, Tool.id == RoomTool.tool_id)
                        .filter(Tool.name == tool_name)
                    )
                    query = query.filter(Classroom.id.in_(has_tool_subquery))

            # Time availability filter
            available_from = filters.get("available_from")
            available_to = filters.get("available_to")

            if available_from and available_to:
                conflicting_reservations = db.session.query(Reservation.room_id).filter(
                    Reservation.start_time < available_to,
                    Reservation.end_time > available_from,
                    Reservation.status.in_(["pending", "active"]),
                )
                query = query.filter(~Classroom.id.in_(conflicting_reservations))

            # Room type filter
            room_type = filters.get("room_type")
            if room_type:
                for type_name in room_type:
                    has_room_subquery = db.session.query(Type.classroom_id).filter(
                        Type.name == type_name
                    )
                    query = query.filter(Classroom.id.in_(has_room_subquery))

            classrooms = query.all()

            return True, {"classrooms": classrooms}

        except Exception:
            return False, "Hiba történt a termek lekérdezése során."

    @staticmethod
    def get_all_classrooms():
        try:
            classrooms = Classroom.query.all()
            return True, {"classrooms": classrooms}
        except Exception:
            return False, "Hiba történt a termek lekérdezése során."

    @staticmethod
    def get_classroom_by_id(classroom_id):
        try:
            classroom = Classroom.query.get(classroom_id)
            if not classroom:
                return False, "A keresett terem nem található."

            return True, classroom
        except Exception:
            return False, "Hiba történt a terem lekérdezésekor."

    @staticmethod
    def create_classroom(data):
        try:
            new_classroom = Classroom(
                id=data.get("id"),
                capacity=data.get("capacity"),
                is_active=True,
                room_type=data.get("type_id"),
            )

            db.session.add(new_classroom)
            db.session.flush()

            tool_ids = data.get("tool_ids", [])
            for tool_id in tool_ids:
                room_tool = RoomTool(
                    classroom_id=new_classroom.id,
                    tool_id=tool_id,
                    quantity=1,
                    active=True,
                )
                db.session.add(room_tool)
            db.session.commit()
            return True, new_classroom
        except Exception as e:
            db.session.rollback()
            return False, str(e)  # "Hiba a terem létrehozásakor." str(e)

    @staticmethod
    def update_classroom(classroom_id, data):
        try:
            classroom = Classroom.query.get(classroom_id)
            if not classroom:
                return False, "A keresett terem nem található."

            if "capacity" in data:
                classroom.capacity = data["capacity"]
            if "is_active" in data:
                classroom.is_active = data["is_active"]
            if "room_type_id" in data:
                classroom.room_type_id = data["room_type_id"]

            if "tools_ids" in data:
                incoming_ids = data["tools_ids"]

                # A .get() üres listát ad vissza, ha a kulcs nem szerepel a kérésben
                incoming_qtys = data.get("tool_quantity", [])
                incoming_acts = data.get("tool_active", [])

                # Jelenlegi eszközök lekérése és szótárba rendezése a gyors eléréshez
                current_room_tools = RoomTool.query.filter_by(
                    classroom_id=classroom.id
                ).all()
                current_tools_dict = {rt.tool_id: rt for rt in current_room_tools}

                # 1. Bejövő ID-k feldolgozása (hozzáadás és frissítés)
                for i, tool_id in enumerate(incoming_ids):
                    # Megnézzük, kaptunk-e az adott indexhez tartozó quantity-t / active státuszt
                    new_qty = incoming_qtys[i] if i < len(incoming_qtys) else None
                    new_act = incoming_acts[i] if i < len(incoming_acts) else None

                    if tool_id in current_tools_dict:
                        # MÁR LÉTEZŐ ESZKÖZ -> Csak azt írjuk felül, amit tényleg megadott a kliens
                        rt = current_tools_dict[tool_id]
                        if new_qty is not None:
                            rt.quantity = new_qty
                        if new_act is not None:
                            rt.active = new_act
                    else:
                        # ÚJ ESZKÖZ -> Ha nem küldött adatot, alapértelmezéseket használunk
                        new_room_tool = RoomTool(
                            classroom_id=classroom.id,
                            tool_id=tool_id,
                            quantity=new_qty if new_qty is not None else 1,
                            active=new_act if new_act is not None else True,
                        )
                        db.session.add(new_room_tool)

                for tool_id, rt in current_tools_dict.items():
                    if rt.quantity == 0:
                        db.session.delete(rt)

            db.session.commit()
            return True, classroom
        except Exception:
            db.session.rollback()
            return False, "Hiba a terem frissítésekor."

    @staticmethod
    def delete_classroom(classroom_id):
        try:
            classroom = Classroom.query.get(classroom_id)
            if not classroom:
                return False, "A keresett terem nem található."

            # Soft delete
            classroom.is_active = False
            # Ha fizikai törlést akarunk: db.session.delete(classroom)

            db.session.commit()
            return True, None
        except Exception:
            db.session.rollback()
            return False, "Hiba a terem törlésekor."
