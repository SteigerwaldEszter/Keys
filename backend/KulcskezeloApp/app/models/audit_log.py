from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"),
                                                nullable=True,
                                                index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_name: Mapped[str  | None] = mapped_column(String(100), nullable=False)
    entity_value: Mapped[str  | None] = mapped_column(String(255))
    new_value: Mapped[str  | None] = mapped_column(Text)
    old_value: Mapped[str  | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column( DateTime(timezone=True), 
                                                server_default=func.now(),
                                                nullable=False,index=True)

    users = relationship("User", back_populates="audit_logs")
