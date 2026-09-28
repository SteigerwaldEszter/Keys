from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class RoomType(db.Model):
    __tablename__ = "room_types"

    room_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), primary_key=True)
    type_id: Mapped[int] = mapped_column(ForeignKey("types.id"), primary_key=True)

    classrooms = relationship("Classroom", back_populates="room_types")
    types = relationship("Type", back_populates="room_types")
