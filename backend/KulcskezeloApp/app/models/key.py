from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class Key(db.Model):
    __tablename__ = "keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="available", nullable=False)
    is_master: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    classroom = relationship("Classroom", back_populates="keys")
    key_logs = relationship("KeyLog", back_populates="key")
