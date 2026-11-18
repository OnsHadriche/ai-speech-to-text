
from datetime import datetime
import uuid
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Float,
    String,
    Text,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DocumentSegment(Base):
    __tablename__ = "document_segments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("document_segments.id", ondelete="SET NULL"),
        nullable=True,
    )
    batch_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("document_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    original_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    suggested_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    suggestion_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    suggestion_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    selected_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    classification_source: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    classification_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="awaiting_confirmation",
        server_default="awaiting_confirmation",
    )

    formatting: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    source_start: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    source_end: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
