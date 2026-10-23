from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Consent(Base):
    __tablename__ = "consent"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # employer_verify | vc_issue | data_share
    consent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    requester_id: Mapped[str | None] = mapped_column(String(36))  # employer or system
    requester_type: Mapped[str | None] = mapped_column(String(20))
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # JSON: fields scope granted or denied
    scope_detail: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
