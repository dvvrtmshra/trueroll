from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Evaluation(Base):
    """Immutable record of one Seat-Ledger evaluation for a course. Never edited."""
    __tablename__ = "evaluation"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    course_approval_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rule_set_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_versions_used: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON
    # OK | RULE_NOT_CONFIRMED | FLAG
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    result_detail: Mapped[str | None] = mapped_column(Text)  # JSON reasons
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
