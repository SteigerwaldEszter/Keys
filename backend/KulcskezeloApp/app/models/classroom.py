from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class Classroom(db.Model):
    __tablename__ = "classrooms"

    id: Mapped[str] = mapped_column(String(10), primary_key=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    room_type: Mapped[int] = mapped_column(Integer, db.ForeignKey("types.id"), nullable=False)

    types = relationship("Type", back_populates="classrooms")
    room_tools = relationship("RoomTool", back_populates="classrooms")
    keys = relationship("Key", back_populates="classrooms")
    reservations = relationship("Reservation", back_populates="classrooms")
    issue_tickets = relationship("IssueTicket", back_populates="classrooms")
