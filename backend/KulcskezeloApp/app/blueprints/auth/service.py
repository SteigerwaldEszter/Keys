from ctypes.wintypes import PINT
from app.models.user import User
from app.models.role import Role
from app.extensions import db
from flask import current_app
from authlib.jose import jwt
from datetime import datetime, timedelta

class AuthService:
    @staticmethod
    def register(data):
        if User.query.filter_by(email=data['email']).first():
            return False, "E-mail már létezik!"
        
        password = data.pop('password')
        role = data.pop('name')
        pin = data.pop('pin')

        role_obj = Role.query.filter_by(name=role).first()
        if not role_obj:
            return False, f"A '{role}' szerepkör nem található az adatbázisban!"

        if role == 'receptionist':
            if not pin:
                return False, "Portás szerepkör létrehozásakor kötelező PIN kódot megadni!"
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
        user = User.query.filter_by(email=data['email']).first()
        if user and user.check_password(data['password']):
            token = AuthService.token_generate(user)
            return True, {"token": token, "user_id": user.id}
        return False, "Hibás hitelesítő adatok!"

    @staticmethod
    def token_generate(user):
        payload = {
            "user_id": user.id,
            "roles": [r.role for r in user.roles],
            "exp": int((datetime.now() + timedelta(hours=8)).timestamp())
        }
        return jwt.encode({'alg': 'RS256'}, payload, current_app.config['SECRET_KEY']).decode()