from pydantic import BaseModel, ConfigDict, Field

from app.schemas.document import DocumentType
from app.schemas.segment import SegmentType


class AIAnalysisSegment(BaseModel):
    """One meaningful segment identified in the transcript."""

    original_text: str = Field(
        min_length=1,
        description=(
            "Exact text copied from the original transcription. "
            "Do not rewrite, summarize, correct, or invent text."
        ),
    )

    suggested_type: SegmentType = Field(
        description=(
            "AI-suggested classification of this transcript segment."
        ),
    )

    suggestion_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence score between 0 and 1."
        ),
    )

    suggestion_reason: str = Field(
        min_length=1,
        description=(
            "Short explanation for the suggested classification."
        ),
    )

    parent_segment_index: int | None = Field(
        description=(
            "Index of the parent heading or section segment "
            "in the segments list. Use null for top-level "
            "segments. Indices start at 0."
        ),
    )

    model_config = ConfigDict(extra="forbid")


class DocumentAnalysisResponse(BaseModel):
    """Structured AI analysis of an educational transcript."""

    document_title: str | None

    subject: str | None

    topic: str | None

    document_type: DocumentType

    segments: list[AIAnalysisSegment] = Field(
        min_length=1,
        description=(
            "Meaningful transcript segments in their exact "
            "original order. Every segment must preserve "
            "the original text."
        ),
    )

    model_config = ConfigDict(extra="forbid")