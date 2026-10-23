from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    # Regional officers: "North", "South", etc.
    region: Mapped[str | None] = mapped_column(String(50))
    # College admins: "INST-0001"
    institution_id: Mapped[str | None] = mapped_column(String(20))
    # Students: FK to student.id (string, not constrained at DB level — see decisions.md D5)
    student_id: Mapped[str | None] = mapped_column(String(36))
    # Employers: FK to employer.id
    employer_id: Mapped[str | None] = mapped_column(String(36))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
