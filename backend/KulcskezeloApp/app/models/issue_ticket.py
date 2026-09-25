from __future__ import annotations

from sqlalchemy import Integer, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app import db


class IssueTicket(db.Model):
    __tablename__ = "issue_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classrooms.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    classroom = relationship("Classroom", back_populates="issue_tickets")
    user = relationship("User", back_populates="issue_tickets")
