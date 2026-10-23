from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class SeatBucket(Base):
    __tablename__ = "seat_bucket"
    __table_args__ = (UniqueConstraint("course_approval_id", "bucket_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    course_approval_id: Mapped[str] = mapped_column(String(50), ForeignKey("course_approval.id"), nullable=False)
    bucket_code: Mapped[str] = mapped_column(String(30), nullable=False)
    cap: Mapped[int] = mapped_column(Integer, nullable=False)
    used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    course: Mapped["CourseApproval"] = relationship(back_populates="seat_buckets")  # noqa: F821
