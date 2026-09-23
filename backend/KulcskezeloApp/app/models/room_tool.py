from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class RoomTool(db.Model):
    __tablename__ = "room_tools"

    classroom_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classrooms.id"), primary_key=True
    )
    tool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tools.id"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    classroom = relationship("Classroom", back_populates="room_tools")
    tool = relationship("Tool", back_populates="room_tools")
