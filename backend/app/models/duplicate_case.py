from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class DuplicateCase(Base):
    __tablename__ = "duplicate_case"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    student_id_a: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    student_id_b: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    match_basis: Mapped[str] = mapped_column(String(30), nullable=False)  # apaar | name_dob | contact
    confidence: Mapped[float | None] = mapped_column()
    # suspected | under_review | confirmed_duplicate | resolved_distinct | resolved_merged
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="suspected")
    resolution_note: Mapped[str | None] = mapped_column(Text)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[str | None] = mapped_column(String(36))
