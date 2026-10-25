"""ShareCode — student-initiated consent code for employer verification (spec 6.7)."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ShareCode(Base):
    __tablename__ = "share_code"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    employer_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)
    # SHA-256 of the 8-char code (XXXX-XXXX without dash)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    # active | withdrawn | expired
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
