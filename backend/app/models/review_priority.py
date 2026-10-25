from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ReviewPriority(Base):
    __tablename__ = "review_priority"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    institution_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    course_id: Mapped[str | None] = mapped_column(String(50), index=True)
    period: Mapped[str] = mapped_column(String(10), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    band: Mapped[str] = mapped_column(String(10), nullable=False, default="Low")  # Low|Medium|High
    reasons: Mapped[str | None] = mapped_column(Text)  # JSON list of {code, detail}
    peer_group: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(String(100), default="robust_baseline + isolation_forest v0.1")
    status: Mapped[str] = mapped_column(String(20), default="advisory")
    officer_label: Mapped[str | None] = mapped_column(String(30))  # useful|not_useful|need_more_info
    features_json: Mapped[str | None] = mapped_column(Text)  # raw feature values for chart data
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
