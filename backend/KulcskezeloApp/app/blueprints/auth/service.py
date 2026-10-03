from datetime import datetime, timedelta

from authlib.jose import jwt
from flask import current_app

from app.extensions import db
from app.models.role import Role
from app.models.user import User


class AuthService:
    @staticmethod
    def register(data):
        if User.query.filter_by(email=data["email"]).first():
            return False, "E-mail már létezik!"

        password = data.pop("password")
        role = data.pop("role")
        pin = data.pop("pin")

        role_obj = Role.query.filter_by(name=role).first()
        if not role_obj:
            return False, f"A '{role}' szerepkör nem található az adatbázisban!"

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

        db.session.add(user)
        db.session.commit()
        return True, user

    @staticmethod
    def login(data):
        user = User.query.filter_by(email=data["email"]).first()
        if user and user.check_password(data["password"]):
            token = AuthService.token_generate(user)
            return True, {"token": token, "user_id": user.id}
        return False, "Hibás hitelesítő adatok!"

    @staticmethod
    def token_generate(user):
        header = {"alg": "RS256"}
        payload = {
            "user_id": user.id,
            "roles": [r.name for r in user.roles],
            "exp": int((datetime.now() + timedelta(hours=8)).timestamp()),
        }
        return jwt.encode(header, payload, current_app.config["PRIVATE_KEY"])

    @staticmethod
    def get_me(user_id):
        user = User.query.get(user_id)
        if not user:
            return False, "A keresett felhasználó nem található."
        return True, {"id": user.id, "name": user.name, "roles": [r.name for r in user.roles]}

    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return False, "A keresett felhasználó nem található."
        db.session.delete(user)
        db.session.commit()
        return True, None
