from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Institution(Base):
    __tablename__ = "institution"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # INST-0001 …
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # Private | Government | Autonomous
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Open")

    courses: Mapped[list["CourseApproval"]] = relationship(back_populates="institution")  # noqa: F821
