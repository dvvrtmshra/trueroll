from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Upload(Base):
    __tablename__ = "upload"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    institution_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    uploaded_by: Mapped[str] = mapped_column(String(36), nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # pending | processing | done | failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Phase 3 fields
    file_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    academic_year: Mapped[str | None] = mapped_column(String(10))
    course_approval_id: Mapped[str | None] = mapped_column(String(50))
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    rows_accepted: Mapped[int] = mapped_column(Integer, default=0)
    rows_warning: Mapped[int] = mapped_column(Integer, default=0)
    rows_errors: Mapped[int] = mapped_column(Integer, default=0)
    identity_tiers: Mapped[str | None] = mapped_column(Text)   # JSON
    duplicates_summary: Mapped[str | None] = mapped_column(Text)  # JSON
    ledger_results: Mapped[str | None] = mapped_column(Text)   # JSON
