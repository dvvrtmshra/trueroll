from datetime import date, datetime
from uuid import uuid4
from sqlalchemy import String, Boolean, Date, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Rule(Base):
    """One canonical rule ID (e.g., SN-A). Has many RuleVersion rows."""
    __tablename__ = "rule"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # SN-A
    current_version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RuleVersion(Base):
    __tablename__ = "rule_version"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    rule_id: Mapped[str] = mapped_column(String(20), default=None, nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)

    # Scope
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)
    programme_level: Mapped[str] = mapped_column(String(100), nullable=False)  # JSON list as str
    domain: Mapped[str] = mapped_column(String(200), nullable=False, default="ALL")
    state: Mapped[str] = mapped_column(String(100), nullable=False, default="ALL")
    institution_type: Mapped[str] = mapped_column(String(50), nullable=False, default="ALL")

    # Bucket definition
    bucket: Mapped[str] = mapped_column(String(30), nullable=False)
    cap_basis: Mapped[str] = mapped_column(String(20), nullable=False, default="approved_intake")
    cap_percent: Mapped[float | None] = mapped_column()
    cap_fixed: Mapped[int | None] = mapped_column()
    eligible_categories: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON

    # Provenance — all illustrative
    source_document: Mapped[str] = mapped_column(Text, nullable=False, default="TO BE CONFIRMED")
    source_clause: Mapped[str] = mapped_column(Text, nullable=False, default="TO BE CONFIRMED")
    source_url: Mapped[str | None] = mapped_column(Text)

    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)

    # draft | pending_review | approved | active | retired
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # JSON array of {by, role, at}
    approvals: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    test_suite: Mapped[str | None] = mapped_column(String(100))

    proposed_by: Mapped[str | None] = mapped_column(String(36))  # user id
    proposed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
