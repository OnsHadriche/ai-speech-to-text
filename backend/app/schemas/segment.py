
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SegmentType = Literal[
    "title",
    "subtitle",
    "heading",
    "subheading",
    "paragraph",
    "definition",
    "example",
    "quotation",
    "list_item",
    "question",
    "answer",
    "exercise_instruction",
    "table",
    "conclusion",
    "other",
]

ClassificationStatus = Literal[
    "detected",
    "suggested",
    "awaiting_confirmation",
    "confirmed",
    "needs_review",
]

ClassificationSource = Literal[
    "user",
    "ai",
]


class SegmentClassificationRequest(BaseModel):
    selected_type: SegmentType

    comment: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional user comment about the classification",
    )


class SegmentUpdateRequest(BaseModel):
    original_text: str | None = None
    selected_type: SegmentType | None = None
    parent_id: str | None = None
    position: int | None = Field(default=None, ge=1)


class SegmentResponse(BaseModel):
    id: str
    document_id: str
    batch_id: str | None = None
    parent_id: str | None = None

    position: int
    original_text: str

    suggested_type: SegmentType | None = None
    suggestion_confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )
    suggestion_reason: str | None = None

    selected_type: SegmentType | None = None
    classification_source: ClassificationSource | None = None
    classification_status: ClassificationStatus

    formatting: dict | None = None

    source_start: int | None = None
    source_end: int | None = None

    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
