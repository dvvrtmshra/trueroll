from datetime import date
from uuid import uuid4
from sqlalchemy import String, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class MatchingPair(Base):
    __tablename__ = "matching_pair"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name_a: Mapped[str] = mapped_column(String(255), nullable=False)
    dob_a: Mapped[date | None] = mapped_column(Date)
    name_b: Mapped[str] = mapped_column(String(255), nullable=False)
    dob_b: Mapped[date | None] = mapped_column(Date)
    is_true_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False)
    typo_type: Mapped[str | None] = mapped_column(String(50))
    pair_group: Mapped[str] = mapped_column(String(10), nullable=False, default="true")
