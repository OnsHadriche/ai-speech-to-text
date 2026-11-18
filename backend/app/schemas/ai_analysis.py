
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.document import DocumentType
from app.schemas.segment import SegmentType


class AIAnalysisSegment(BaseModel):
    """One meaningful segment identified in the transcript."""

    original_text: str = Field(
        min_length=1,
        description="Exact text copied from the original transcription.",
    )

    suggested_type: SegmentType = Field(
        description="AI-suggested educational segment classification.",
    )

    suggestion_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1.",
    )

    suggestion_reason: str = Field(
        min_length=1,
        description="Short explanation for the suggested classification.",
    )

    model_config = ConfigDict(extra="forbid")


class DocumentAnalysisResponse(BaseModel):
    """Structured AI analysis of an Arabic educational transcript."""

    document_title: str | None = None
    subject: str | None = None
    topic: str | None = None

    document_type: DocumentType

    segments: list[AIAnalysisSegment] = Field(
        min_length=1,
        description="Meaningful segments in their original order.",
    )

    model_config = ConfigDict(extra="forbid")
