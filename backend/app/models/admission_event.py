from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class AdmissionEvent(Base):
    """Immutable event log. Counters in SeatBucket are derived from this."""
    __tablename__ = "admission_event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("student.id"), nullable=False)
    course_approval_id: Mapped[str] = mapped_column(String(50), ForeignKey("course_approval.id"), nullable=False)
    seat_category: Mapped[str] = mapped_column(String(30), nullable=False)
    # ADMIT | WITHDRAW | TRANSFER | CORRECTION
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # ROUND_1 | ROUND_2 | ROUND_3 | SPOT
    admission_round: Mapped[str] = mapped_column(String(10), nullable=False, default="ROUND_1")
    # REGULAR | LATERAL
    entry_type: Mapped[str] = mapped_column(String(10), nullable=False, default="REGULAR")
    nationality_status: Mapped[str] = mapped_column(String(10), nullable=False, default="INDIAN")
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    upload_id: Mapped[str | None] = mapped_column(String(36))

    course: Mapped["CourseApproval"] = relationship(back_populates="admission_events")  # noqa: F821
