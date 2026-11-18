
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    subject: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    topic: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    document_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="ar",
        server_default="ar",
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="transcribed",
        server_default="transcribed",
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
