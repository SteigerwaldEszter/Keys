from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app import db


class Signature(db.Model):
    __tablename__ = "signatures"

    id: Mapped[int] = mapped_column(primary_key=True)
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    signed_at: Mapped[datetime] = mapped_column(server_default=func.now())

    key_log = relationship("KeyLog", back_populates="signature")