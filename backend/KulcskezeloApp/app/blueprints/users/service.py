from app.blueprints.reports.service import create_audit_log
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
            user = db.session.get(User, user_id)

            if not user:
                return False, "Felhasználó nem található."

            user_data = {
                "id": user.id,
                "name": user.name,
                "roles": [role.name for role in user.roles],
            }

            return True, user_data

        except Exception:
            return False, "Hiba a felhasználó lekérdezésekor."

    @staticmethod
    def update_user_roles(
        user_id,
        json_data,
        actor_user_id,
    ):
        try:
            user = db.session.get(User, user_id)

            if not user:
                return False, "Felhasználó nem található."

            role_names = json_data.get("role_names", [])

            if not role_names:
                return False, "Legalább egy szerepkör szükséges."

            if len(role_names) != len(set(role_names)):
                return False, "A szerepkörök nem ismétlődhetnek."

            roles = db.session.query(Role).filter(Role.name.in_(role_names)).all()

            found_roles = {role.name for role in roles}

            for role_name in role_names:
                if role_name not in found_roles:
                    return (
                        False,
                        f"A '{role_name}' szerepkör nem található.",
                    )

            old_roles = sorted(role.name for role in user.roles)

            new_roles = sorted(role_names)

            if old_roles == new_roles:
                return True, {
                    "id": user.id,
                    "name": user.name,
                    "roles": old_roles,
                }

            user.roles = roles

            create_audit_log(
                action="USER_ROLES_UPDATED",
                entity_name="users",
                entity_value=user.id,
                user_id=actor_user_id,
                old_value={
                    "roles": old_roles,
                },
                new_value={
                    "roles": new_roles,
                },
            )

            db.session.commit()

            return True, {
                "id": user.id,
                "name": user.name,
                "roles": new_roles,
            }

        except Exception:
            db.session.rollback()
            return (
                False,
                "Hiba a felhasználó szerepkörének frissítésekor.",
            )
