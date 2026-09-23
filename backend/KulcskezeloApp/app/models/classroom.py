from __future__ import annotations

from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class Classroom(db.Model):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    room_types = relationship("RoomType", back_populates="classroom")
    room_tools = relationship("RoomTool", back_populates="classroom")
    keys = relationship("Key", back_populates="classroom")
    reservations = relationship("Reservation", back_populates="classroom")
    issue_tickets = relationship("IssueTicket", back_populates="classroom")
