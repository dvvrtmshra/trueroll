from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4
from app.models.base import Base


class AnomalyLabel(Base):
    __tablename__ = "anomaly_label"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    institution_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    course_id: Mapped[str | None] = mapped_column(String(50))
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)
    # LATE_SURGE|CATEGORY_MIX|SHARED_ATTRIBUTE_CLUSTER|FULL_STREAK|POST_AUDIT_WITHDRAWALS|NONE
    anomaly_type: Mapped[str] = mapped_column(String(50), nullable=False, default="NONE")
    planted: Mapped[bool] = mapped_column(Boolean, default=True)
