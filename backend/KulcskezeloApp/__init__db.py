from __future__ import annotations

from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.classroom import Classroom
from app.models.issue_ticket import IssueTicket
from app.models.key import Key
from app.models.key_log import KeyLog
from app.models.reservation import Reservation
from app.models.role import Role
from app.models.room_tool import RoomTool
from app.models.room_type import RoomType
from app.models.signature import Signature
from app.models.tool import Tool
from app.models.type import Type
from app.models.user import User
from app.models.user_role import UserRole
from config import Config

app = create_app(config_class=Config)


def seed_database():
    with app.app_context():
        try:
            db.drop_all()
            db.create_all()
            # Role
            if not Role.query.filter_by(name="Admin").first():
                db.session.add_all(
                    [
                        Role(name="Admin"),
                        Role(name="Instructor"),
                        Role(name="Director"),
                        Role(name="Receptionist"),
                    ]
                )
                db.session.commit()
            # Type
            if not Type.query.filter_by(name="Labor").first():
                db.session.add_all(
                    [Type(id=1, name="Lab"), Type(id=2, name="Seminar Room")]
                )
                db.session.commit()
            # Tool
            if not Tool.query.filter_by(name="Projector").first():
                db.session.add_all(
                    [
                        Tool(id=1, name="Projector", active=True),
                        Tool(id=2, name="Interactive Whiteboard", active=True),
                        Tool(id=3, name="Whiteboard marker", active=True),
                        Tool(id=4, name="Remote Controller", active=False),
                    ]
                )
                db.session.commit()

            test_users = [
                {
                    "email": "admin@teszt.hu",
                    "name": "Admin Adrián",
                    "password": "Password123",
                    "pin": "",
                    "roles": "Admin"
                },
                {
                    "email": "eloado.elod@teszt.hu",
                    "name": "Előadó Előd",
                    "password": "Password123",
                    "pin": "",
                    "roles": "Instructor"
                },
                {
                    "email": "fnoi.feri@teszt.hu",
                    "name": "Főnök Ferenc",
                    "password": "Password123",
                    "pin": "",
                    "roles": "Director"
                },
                {
                    "email": "portas@teszt.hu",
                    "name": "Portás Péter",
                    "password": "Password123",
                    "pin": "1234",
                    "roles": "Receptionist"
                },
            ]
            # user
            for u_data in test_users:
                if not User.query.filter_by(email=u_data["email"]).first():
                    user = User(
                        name=u_data["name"],
                        email=u_data["email"],
                    )
                    user.set_password(u_data["password"])
                    user.set_pin(u_data["pin"])
                    db.session.add(user)
                    db.session.commit()

                    role = Role.query.filter_by(name=u_data["roles"]).first()
                    if role:
                        user_role = UserRole(user_id=user.id, role_id=role.id)
                        db.session.add(user_role)
                        db.session.commit()
            # Classroom
            if not Classroom.query.first():
                c1 = Classroom(capacity=60, is_active=True)
                c2 = Classroom(capacity=24, is_active=True)
                c3 = Classroom(capacity=16, is_active=True)
                db.session.add_all([c1, c2, c3])
                db.session.commit()
            # room type
            c1 = Classroom.query.filter_by(capacity=60).first()
            c2 = Classroom.query.filter_by(capacity=24).first()
            t_lab = Type.query.filter_by(name="Lab").first()
            t_seminar = Type.query.filter_by(name="Seminar Room").first()

            if not RoomType.query.first() and c1 and c2 and t_lab and t_seminar:
                db.session.add_all(
                    [
                        RoomType(room_id=c1.id, type_id=t_seminar.id),
                        RoomType(room_id=c2.id, type_id=t_lab.id),
                    ]
                )
                db.session.commit()
            # roomtool
            tool_proj = Tool.query.filter_by(name="Projector").first()
            tool_pen = Tool.query.filter_by(name="Whiteboard marker").first()

            if not RoomTool.query.first() and tool_proj and tool_pen and c1 and c2:
                db.session.add_all(
                    [
                        RoomTool(classroom_id=c1.id, tool_id=tool_proj.id, quantity=1),
                        RoomTool(classroom_id=c1.id, tool_id=tool_pen.id, quantity=4),
                        RoomTool(classroom_id=c2.id, tool_id=tool_proj.id, quantity=1),
                    ]
                )
                db.session.commit()
            # key
            if not Key.query.first() and c1 and c2:
                db.session.add_all(
                    [
                        Key(
                            room_id=c1.id,
                            name="101-A",
                            status="available",
                            is_master=False,
                        ),
                        Key(
                            room_id=c2.id,
                            name="LAB-01",
                            status="taken",
                            is_master=False,
                        ),
                        Key(
                            room_id=c1.id,
                            name="FŐKULCS",
                            status="available",
                            is_master=True,
                        ),
                    ]
                )
                db.session.commit()
            # Reservation
            instructor = User.query.filter_by(email="oktato@teszt.hu").first()
            if not Reservation.query.first() and instructor and c2:
                res = Reservation(
                    user_id=instructor.id,
                    room_id=c2.id,
                    start_time=datetime.now() + timedelta(days=1, hours=2),
                    end_time=datetime.now() + timedelta(days=1, hours=4),
                    status="approved",
                )
                db.session.add(res)
                db.session.commit()
            # Signature
            key_lab = Key.query.filter_by(name="LAB-01").first()
            reservation = Reservation.query.first()
            receptionist = User.query.filter_by(email="portas@teszt.hu").first()

            if not Signature.query.first():
                sig = Signature(
                    format="svg", payload="data:image/svg+xml;base64,PHN2ZyB4bWxucz0..."
                )
                db.session.add(sig)
                db.session.commit()

                if key_lab and reservation and receptionist and instructor:
                    db.session.add(
                        KeyLog(
                            key_id=key_lab.id,
                            reservation_id=reservation.id,
                            handler_id=receptionist.id,
                            receiver_id=instructor.id,
                            signature_id=sig.id,
                            action="take",
                        )
                    )
                    db.session.commit()
            # IssueTicket
            if not IssueTicket.query.first() and instructor and c2:
                db.session.add(
                    IssueTicket(
                        room_id=c2.id,
                        user_id=instructor.id,
                        title="Távirányító nem működik",
                        description="A projektorhoz tartozó távirányító lemerült.",
                        status="open",
                    )
                )
                db.session.commit()
            # audit_log
            admin = User.query.filter_by(email="admin@teszt.hu").first()
            if not AuditLog.query.first() and admin and c1:
                db.session.add(
                    AuditLog(
                        user_id=admin.id,
                        action="CREATE",
                        entity_name="Classroom",
                        entity_value=str(c1.id),
                        new_value='{"capacity": 60, "is_active": true}',
                        old_value="",
                    )
                )
                db.session.commit()

            print("lefutott")
        except Exception as e:
            db.session.rollback()
            print(f"\nHIBA A feltöltés megszakadt egy hiba miatt: {e}")
            raise


if __name__ == "__main__":
    seed_database()
