from __future__ import annotations

from sqlalchemy import Integer, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class MasterKeyRooms(db.Model):
    __tablename__ = "master_key_rooms"

    key_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("keys.id"), primary_key=True
    )
    room_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("classrooms.id"), primary_key=True
    )

    keys = relationship("Key", back_populates="master_key_rooms")
    rooms = relationship("Classroom", back_populates="master_key_rooms")
