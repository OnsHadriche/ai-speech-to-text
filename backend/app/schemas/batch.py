from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


BatchStatus = Literal[
    "pending",
    "presented",
    "in_progress",
    "completed",
    "skipped",
]


class BatchCreate(BaseModel):
    document_id: str = Field(min_length=36, max_length=36)
    batch_number: int = Field(ge=1)


class BatchResponse(BaseModel):
    id: str
    document_id: str
    batch_number: int
    status: BatchStatus
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BatchClassificationRequest(BaseModel):
    segment_id: str = Field(min_length=36, max_length=36)
    selected_type: str
    comment: str | None = Field(default=None, max_length=1000)


class BatchSubmissionRequest(BaseModel):
    classifications: list[BatchClassificationRequest] = Field(
        min_length=1,
        max_length=5,
    )