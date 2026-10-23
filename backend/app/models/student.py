from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import String, Date, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Student(Base):
    __tablename__ = "student"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(20))
    apaar_id: Mapped[str | None] = mapped_column(String(12), index=True)  # 12 digits or NULL
    identity_tier: Mapped[str] = mapped_column(String(5), nullable=False, default="T3")
    # Keyed HMAC tokens — raw values are never stored
    contact_token: Mapped[str | None] = mapped_column(String(64))
    guardian_token: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
