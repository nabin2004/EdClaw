from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Fact(Base):
    __tablename__ = "fact"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    subject: Mapped[str] = mapped_column(String, index=True)
    predicate: Mapped[str] = mapped_column(String)
    object: Mapped[str] = mapped_column(String)
    valid_from: Mapped[datetime] = mapped_column(DateTime)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    superseded_by: Mapped[str | None] = mapped_column(ForeignKey("fact.id"), nullable=True)
    source_log_id: Mapped[str | None] = mapped_column(ForeignKey("embedded_log.id"), nullable=True)

    __table_args__ = (Index("ix_fact_subject_valid", "subject", "valid_from", "valid_until"),)


class EmbeddedLog(Base):
    __tablename__ = "embedded_log"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)
    ts: Mapped[datetime] = mapped_column(DateTime)
    text: Mapped[str] = mapped_column(String)


class IrNodeRow(Base):
    """Indexed IR nodes (denormalized for MVP)."""

    __tablename__ = "ir_node"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    objective: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    yaml_blob: Mapped[str] = mapped_column(String, default="")
