from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app import db
# from app.models.user import User


class Role(db.Model):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # user_roles = relationship("UserRole", back_populates="roles")
    users: Mapped[List["User"]] = relationship(
        secondary="user_roles", back_populates="roles"
    )
