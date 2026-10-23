from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class CourseApproval(Base):
    __tablename__ = "course_approval"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # INST-0001-CSE-2026
    institution_id: Mapped[str] = mapped_column(String(20), ForeignKey("institution.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)   # Diploma|UG|PG|MBA/PGDM|MCA
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)  # 2026-27
    approved_intake: Mapped[int] = mapped_column(Integer, nullable=False)
    lateral_intake: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    institution: Mapped["Institution"] = relationship(back_populates="courses")  # noqa: F821
    seat_buckets: Mapped[list["SeatBucket"]] = relationship(back_populates="course")  # noqa: F821
    admission_events: Mapped[list["AdmissionEvent"]] = relationship(back_populates="course")  # noqa: F821
