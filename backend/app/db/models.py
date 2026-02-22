"""
app/db/models.py — SQLAlchemy ORM models.

Tables:
  reviews        — one row per PR reviewed
  review_comments — individual issues found
  code_embeddings — pgvector table for RAG

PHASE 7 — Used once DB is connected.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Review(Base):
    __tablename__ = "reviews"

    id:             Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_name:      Mapped[str]        = mapped_column(String(255), index=True)
    pr_number:      Mapped[int]        = mapped_column(Integer)
    pr_title:       Mapped[str]        = mapped_column(String(500), nullable=True)
    pr_author:      Mapped[str]        = mapped_column(String(100), nullable=True)
    reviewed_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), default=utcnow)
    approved:       Mapped[bool]       = mapped_column(Boolean, default=False)
    critical_count: Mapped[int]        = mapped_column(Integer, default=0)
    warning_count:  Mapped[int]        = mapped_column(Integer, default=0)
    suggestion_count: Mapped[int]      = mapped_column(Integer, default=0)
    summary:        Mapped[str]        = mapped_column(Text, nullable=True)

    comments: Mapped[list["ReviewComment"]] = relationship(back_populates="review", cascade="all, delete-orphan")


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id:   Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id"), index=True)
    file_path:   Mapped[str]       = mapped_column(String(500))
    line_number: Mapped[int]       = mapped_column(Integer, nullable=True)
    severity:    Mapped[str]       = mapped_column(String(20))  # critical/warning/suggestion
    title:       Mapped[str]       = mapped_column(String(300))
    body:        Mapped[str]       = mapped_column(Text)
    suggestion:  Mapped[str]       = mapped_column(Text, nullable=True)

    review: Mapped["Review"] = relationship(back_populates="comments")


class CodeEmbedding(Base):
    """pgvector table for RAG — stores embedded code chunks."""
    __tablename__ = "code_embeddings"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id:   Mapped[str]       = mapped_column(String(500), unique=True, index=True)
    file_path:  Mapped[str]       = mapped_column(String(500), index=True)
    content:    Mapped[str]       = mapped_column(Text)
    start_line: Mapped[int]       = mapped_column(Integer)
    end_line:   Mapped[int]       = mapped_column(Integer)
    # pgvector column — 384 dims for all-MiniLM-L6-v2
    embedding = mapped_column(
        __import__("pgvector.sqlalchemy", fromlist=["Vector"]).Vector(384),
        nullable=True,
    )
