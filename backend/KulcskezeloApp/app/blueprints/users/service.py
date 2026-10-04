from app.extensions import db
from app.models.role import Role
from app.models.user import User


class UserService:
    @staticmethod
    def get_all_users():
        try:
            users = User.query.all()
            user_list = [
                {
                    "id": user.id,
                    "name": user.name,
                    "roles": [role.name for role in user.roles],
                }
                for user in users
            ]
            return True, {"users": user_list}
        except Exception:
            return False, "Hiba a felhasználók lekérdezésekor."

    @staticmethod
    def get_user_by_id(user_id):
        try:
            user = User.query.get(user_id)
            if user:
                user_data = {
                    "id": user.id,
                    "name": user.name,
                    "roles": [role.name for role in user.roles],
                }
                return True, user_data
            return False, "Felhasználó nem található."
        except Exception:
            return False, "Hiba a felhasználó lekérdezésekor."

    @staticmethod
    def update_user_roles(user_id, json_data):
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "Felhasználó nem található."

            role_names = json_data.get("role_names", [])

            user.roles.clear()

            for role_name in role_names:
                role = db.session.query(Role).filter_by(name=role_name).first()
                if role:
                    user.roles.append(role)
                else:
                    return False, f"A '{role_name}' szerepkör nem található."

            db.session.commit()
            return True, {
                "id": user.id,
                "name": user.name,
                "roles": [role.name for role in user.roles],
            }
        except Exception:
            db.session.rollback()
            return False, "Hiba a felhasználó szerepkörének frissítésekor."
