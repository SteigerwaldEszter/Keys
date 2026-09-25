from __future__ import annotations

from sqlalchemy import Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app import db


class KeyLog(db.Model):
    __tablename__ = "key_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_id: Mapped[int] = mapped_column(Integer, ForeignKey("keys.id"), nullable=False)
    reservation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reservations.id"), nullable=False
    )
    handler_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    receiver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    signature_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("signatures.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(server_default=func.now())

    key = relationship("Key", back_populates="key_logs")
    reservation = relationship("Reservation", back_populates="key_logs")
    handler = relationship(
        "User", foreign_keys=[handler_id], back_populates="handled_key_logs"
    )
    receiver = relationship(
        "User", foreign_keys=[receiver_id], back_populates="received_key_logs"
    )
    signature = relationship("Signature", back_populates="key_logs")
