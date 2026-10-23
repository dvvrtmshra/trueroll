from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Flag(Base):
    __tablename__ = "flag"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    institution_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    course_approval_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    bucket: Mapped[str] = mapped_column(String(30), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(20))
    rule_version: Mapped[int | None] = mapped_column(Integer)
    evaluation_id: Mapped[str | None] = mapped_column(String(36))
    cap: Mapped[int | None] = mapped_column(Integer)
    used: Mapped[int | None] = mapped_column(Integer)
    over_by: Mapped[int | None] = mapped_column(Integer)
    record_ids: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of student IDs
    # open | under_review | clarification_requested | resolved | escalated | auto_cleared
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="high")
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    first_breach_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_officer: Mapped[str | None] = mapped_column(String(36))
    decision: Mapped[str | None] = mapped_column(String(30))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
