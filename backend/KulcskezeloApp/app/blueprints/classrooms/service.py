from app.blueprints.reports.service import create_audit_log
from app.extensions import db
from app.models.classroom import Classroom
from app.models.reservation import Reservation
from app.models.room_tool import RoomTool
from app.models.tool import Tool
from app.models.type import Type


def classroom_audit_data(classroom):
    room_tools = (
        RoomTool.query.filter_by(classroom_id=classroom.id)
        .order_by(RoomTool.tool_id)
        .all()
    )

    return {
        "id": classroom.id,
        "capacity": classroom.capacity,
        "is_active": classroom.is_active,
        "room_type": classroom.room_type,
        "tools": [
            {
                "tool_id": rt.tool_id,
                "quantity": rt.quantity,
                "active": rt.active,
            }
            for rt in room_tools
        ],
    }


class ClassroomService:
    @staticmethod
    def get_filtered_classrooms(filters):
        try:
            query = Classroom.query.filter(Classroom.is_active.is_(True))

            capacity_min = filters.get("capacity_min")

            if capacity_min:
                query = query.filter(Classroom.capacity >= capacity_min)

            tools = filters.get("tools")

            if tools:
                for tool_name in tools:
                    has_tool_subquery = (
                        db.session.query(RoomTool.classroom_id)
                        .join(Tool, Tool.id == RoomTool.tool_id)
                        .filter(
                            Tool.name == tool_name,
                            RoomTool.active.is_(True),
                        )
                    )

                    query = query.filter(Classroom.id.in_(has_tool_subquery))

            available_from = filters.get("available_from")
            available_to = filters.get("available_to")

            if available_from and available_to:
                if available_from >= available_to:
                    return (False, "A keresési időintervallum érvénytelen.")

                conflicting_reservations = db.session.query(Reservation.room_id).filter(
                    Reservation.start_time < available_to,
                    Reservation.end_time > available_from,
                    Reservation.status.in_(["pending", "active"]),
                )

                query = query.filter(~Classroom.id.in_(conflicting_reservations))

            room_type = filters.get("room_type")

            if room_type:
                query = query.join(Type, Type.id == Classroom.room_type).filter(
                    Type.name == room_type
                )

            return True, {"classrooms": query.all()}

        except Exception:
            return (False, "Hiba történt a termek lekérdezése során.")

    @staticmethod
    def get_all_classrooms():
        try:
            return True, {"classrooms": Classroom.query.all()}

        except Exception:
            return (False, "Hiba történt a termek lekérdezése során.")

    @staticmethod
    def get_classroom_by_id(classroom_id):
        try:
            classroom = db.session.get(Classroom, classroom_id)

            if classroom is None:
                return (False, "A keresett terem nem található.")

            return True, classroom

        except Exception:
            return (False, "Hiba történt a terem lekérdezésekor.")

    @staticmethod
    def create_classroom(data, actor_user_id):
        try:
            new_classroom = Classroom(
                id=data.get("id"),
                capacity=data.get("capacity"),
                is_active=True,
                room_type=data.get("type_id"),
            )

            db.session.add(new_classroom)
            db.session.flush()

            for tool_id in data.get("tool_ids", []):
                db.session.add(
                    RoomTool(
                        classroom_id=new_classroom.id,
                        tool_id=tool_id,
                        quantity=1,
                        active=True,
                    )
                )

            db.session.flush()

            create_audit_log(
                action="CLASSROOM_CREATED",
                entity_name="classrooms",
                entity_value=new_classroom.id,
                user_id=actor_user_id,
                new_value=classroom_audit_data(new_classroom),
            )

            db.session.commit()
            return True, new_classroom

        except Exception as exc:
            db.session.rollback()
            return False, str(exc)

    @staticmethod
    def update_classroom(
        classroom_id,
        data,
        actor_user_id,
    ):
        try:
            classroom = db.session.get(Classroom, classroom_id)

            if classroom is None:
                return (False, "A keresett terem nem található.")

            old_data = classroom_audit_data(classroom)

            if "capacity" in data:
                classroom.capacity = data["capacity"]

            if "is_active" in data:
                classroom.is_active = data["is_active"]

            if "room_type_id" in data:
                classroom.room_type = data["room_type_id"]

            if "tools_ids" in data:
                incoming_ids = data["tools_ids"]
                incoming_qtys = data.get("tool_quantity", [])
                incoming_acts = data.get("tool_active", [])

                current_room_tools = RoomTool.query.filter_by(
                    classroom_id=classroom.id
                ).all()

                current_tools_dict = {rt.tool_id: rt for rt in current_room_tools}

                for index, tool_id in enumerate(incoming_ids):
                    new_qty = (
                        incoming_qtys[index] if index < len(incoming_qtys) else None
                    )

                    new_act = (
                        incoming_acts[index] if index < len(incoming_acts) else None
                    )

                    if tool_id in current_tools_dict:
                        rt = current_tools_dict[tool_id]

                        if new_qty == 0:
                            db.session.delete(rt)
                            continue

                        if new_qty is not None:
                            rt.quantity = new_qty

                        if new_act is not None:
                            rt.active = new_act

                    elif new_qty != 0:
                        db.session.add(
                            RoomTool(
                                classroom_id=classroom.id,
                                tool_id=tool_id,
                                quantity=(new_qty if new_qty is not None else 1),
                                active=(new_act if new_act is not None else True),
                            )
                        )

            db.session.flush()

            new_data = classroom_audit_data(classroom)

            if old_data != new_data:
                create_audit_log(
                    action="CLASSROOM_UPDATED",
                    entity_name="classrooms",
                    entity_value=classroom.id,
                    user_id=actor_user_id,
                    old_value=old_data,
                    new_value=new_data,
                )

            db.session.commit()
            return True, classroom

        except Exception:
            db.session.rollback()
            return (False, "Hiba a terem frissítésekor.")

    @staticmethod
    def delete_classroom(
        classroom_id,
        actor_user_id,
    ):
        try:
            classroom = db.session.get(Classroom, classroom_id)

            if classroom is None:
                return (False, "A keresett terem nem található.")

            if not classroom.is_active:
                return True, None

            old_data = classroom_audit_data(classroom)

            classroom.is_active = False
            db.session.flush()

            create_audit_log(
                action="CLASSROOM_DEACTIVATED",
                entity_name="classrooms",
                entity_value=classroom.id,
                user_id=actor_user_id,
                old_value=old_data,
                new_value=classroom_audit_data(classroom),
            )

            db.session.commit()
            return True, None

        except Exception:
            db.session.rollback()
            return (False, "Hiba a terem törlésekor.")
