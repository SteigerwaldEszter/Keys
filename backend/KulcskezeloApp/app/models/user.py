from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from typing import List

#from app.models.role import Role
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    roles: Mapped[List['Role']] = relationship( secondary='user_roles', back_populates='users')
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    pin_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    issue_tickets = relationship("IssueTicket", back_populates="users")
    #user_roles = relationship("UserRole", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="users")
    reservations = relationship("Reservation", back_populates="users")

    handled_key_logs = relationship("KeyLog", foreign_keys="[KeyLog.handler_id]", back_populates="handlers")
    received_key_logs = relationship("KeyLog", foreign_keys="[KeyLog.receiver_id]", back_populates="receivers")
   
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_pin(self, pin: str) -> None:
        self.pin_hash = generate_password_hash(pin)

    def check_pin(self, pin):
        return check_password_hash(self.pin_hash, pin)
