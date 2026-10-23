from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ReviewPriority(Base):
    __tablename__ = "review_priority"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    flag_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # JSON: days_open, over_by, flag_count, ...
    score_breakdown: Mapped[str | None] = mapped_column(Text)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
