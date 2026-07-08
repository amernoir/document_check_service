import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Check(Base):
    __tablename__ = "checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    program: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    status_label: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    documents: Mapped[list["Document"]] = relationship(back_populates="check", cascade="all, delete-orphan")
    issues: Mapped[list["CheckIssue"]] = relationship(back_populates="check", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_id: Mapped[str] = mapped_column(String(36), ForeignKey("checks.id"))
    filename: Mapped[str] = mapped_column(String(255))
    detected_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500))
    size_kb: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    check: Mapped["Check"] = relationship(back_populates="documents")


class CheckIssue(Base):
    __tablename__ = "check_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_id: Mapped[str] = mapped_column(String(36), ForeignKey("checks.id"))
    level: Mapped[str] = mapped_column(String(10))
    message: Mapped[str] = mapped_column(Text)

    check: Mapped["Check"] = relationship(back_populates="issues")
