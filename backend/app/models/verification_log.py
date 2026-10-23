from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class VerificationLog(Base):
    __tablename__ = "verification_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    credential_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    employer_id: Mapped[str | None] = mapped_column(String(36))
    verifier_did: Mapped[str | None] = mapped_column(Text)
    # Fields requested — JSON list, must be minimal per spec 6.7
    fields_requested: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    result: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(50))
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
