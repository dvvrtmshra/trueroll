"""VerificationEvent — per-check log for share-code verifications (spec 6.7)."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class VerificationEvent(Base):
    __tablename__ = "verification_event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    share_code_id: Mapped[str | None] = mapped_column(String(36), index=True)
    employer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    result: Mapped[str] = mapped_column(String(40), nullable=False)
    # VERIFIED | EXPIRED | WITHDRAWN | NOT_FOR_THIS_VERIFIER | NOT_FOUND | INVALID_SIGNATURE
    verification_id: Mapped[str] = mapped_column(String(20), nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
