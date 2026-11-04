from __future__ import annotations

from sqlalchemy import Integer, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class MasterKeyPermissions(db.Model):
    __tablename__ = "master_key_permissions"

    key_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("keys.id"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )

    keys = relationship("Key", back_populates="master_key_permissions")
    users = relationship("User", back_populates="master_key_permissions")
