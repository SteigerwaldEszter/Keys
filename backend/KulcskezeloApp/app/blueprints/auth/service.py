from datetime import datetime, timedelta

from authlib.jose import jwt
from flask import current_app

from app.blueprints.reports.service import create_audit_log
from app.extensions import db
from app.models.role import Role
from app.models.user import User


class AuthService:
    @staticmethod
    def register(data, actor_user_id):
        data = dict(data)

        if User.query.filter_by(email=data["email"]).first():
            return False, "E-mail már létezik!"

        password = data.pop("password")
        role = data.pop("role")
        pin = data.pop("pin", None)

        role_obj = Role.query.filter_by(name=role).first()

        if not role_obj:
            return False, (f"A '{role}' szerepkör nem található az adatbázisban!")

        if role == "Receptionist":
            if not pin:
                return (
                    False,
                    "Portás szerepkör létrehozásakor kötelező PIN kódot megadni!",
                )
        else:
            pin = None

        user = User(**data)
        user.set_password(password)

        if pin:
            user.set_pin(pin)

        user.roles.append(role_obj)

        try:
            db.session.add(user)
            db.session.flush()

            create_audit_log(
                action="USER_CREATED",
                entity_name="users",
                entity_value=user.id,
                user_id=actor_user_id,
                new_value={
                    "created_user_id": user.id,
                    "role": role,
                },
            )

            db.session.commit()
            return True, user

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def login(data):
        user = User.query.filter_by(email=data["email"]).first()

        if user and user.check_password(data["password"]):
            token = AuthService.token_generate(user)

            create_audit_log(
                action="LOGIN_SUCCESS",
                entity_name="authentication",
                entity_value=user.id,
                user_id=user.id,
            )

            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise

            return True, {
                "token": token,
                "user_id": user.id,
            }

        create_audit_log(
            action="LOGIN_FAILED",
            entity_name="authentication",
            entity_value=user.id if user else None,
            user_id=None,
            new_value={
                "reason": "invalid_credentials",
            },
        )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return False, "Hibás hitelesítő adatok!"

    @staticmethod
    def record_logout(user_id):
        create_audit_log(
            action="LOGOUT_REQUESTED",
            entity_name="authentication",
            entity_value=user_id,
            user_id=user_id,
        )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def token_generate(user):
        header = {"alg": "RS256"}

        payload = {
            "user_id": user.id,
            "roles": [r.name for r in user.roles],
            "exp": int((datetime.now() + timedelta(hours=8)).timestamp()),
        }

        return jwt.encode(
            header,
            payload,
            current_app.config["PRIVATE_KEY"],
        )

    @staticmethod
    def get_me(user_id):
        user = User.query.get(user_id)

        if not user:
            return False, ("A keresett felhasználó nem található.")

        return True, {
            "id": user.id,
            "name": user.name,
            "roles": [r.name for r in user.roles],
        }

    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)

        if not user:
            return False, ("A keresett felhasználó nem található.")

        db.session.delete(user)
        db.session.commit()

        return True, None
