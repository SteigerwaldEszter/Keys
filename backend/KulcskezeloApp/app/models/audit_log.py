from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_value: Mapped[str] = mapped_column(String(255))
    new_value: Mapped[str] = mapped_column(Text)
    old_value: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now())

    user = relationship("User", back_populates="audit_logs")
