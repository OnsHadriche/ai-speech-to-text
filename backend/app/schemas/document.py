
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


DocumentStatus = Literal[
    "transcribed",
    "analyzing",
    "classification_in_progress",
    "review_required",
    "ready_for_generation",
    "generated",
    "failed",
]

DocumentType = Literal[
    "essay",
    "lesson",
    "summary",
    "exercises",
    "argumentative_text",
    "other",
]


class DocumentCreate(BaseModel):
    job_id: str = Field(
        min_length=36,
        max_length=36,
        description="ID of the completed transcription job",
    )

    language: str = Field(
        default="ar",
        max_length=10,
    )


class DocumentResponse(BaseModel):
    id: str
    job_id: str

    title: str | None = None
    subject: str | None = None
    topic: str | None = None

    document_type: DocumentType | None = None
    language: str

    status: DocumentStatus

    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
