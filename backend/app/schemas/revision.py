from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RevisionAction = Literal[
    "classification_changed",
    "text_corrected",
    "segment_created",
    "segment_deleted",
    "segment_split",
    "segments_merged",
    "segment_reordered",
    "parent_changed",
]


class RevisionCreate(BaseModel):
    document_id: str = Field(min_length=36, max_length=36)
    segment_id: str | None = None
    action: RevisionAction
    old_value: dict | None = None
    new_value: dict | None = None
    description: str | None = Field(default=None, max_length=2000)


class RevisionResponse(BaseModel):
    id: str
    document_id: str
    segment_id: str | None = None
    action: RevisionAction
    old_value: dict | None = None
    new_value: dict | None = None
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)