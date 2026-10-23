from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Credential(Base):
    """Verifiable credential (VC) issued to a student. Signed with Ed25519 key."""
    __tablename__ = "credential"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    admission_event_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # admission | enrollment_year | completion
    credential_type: Mapped[str] = mapped_column(String(30), nullable=False)
    did: Mapped[str] = mapped_column(Text, nullable=False)  # did:trueroll:<uuid>
    vc_jwt: Mapped[str] = mapped_column(Text, nullable=False)
    public_key_kid: Mapped[str] = mapped_column(String(100), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(Text)
