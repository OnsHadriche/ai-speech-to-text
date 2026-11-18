
from typing import Any, Literal, TypedDict


class EducationalAgentState(TypedDict, total=False):
    """
    Shared state passed between LangGraph workflow nodes.

    PostgreSQL remains the source of truth.
    This state carries the data needed during one workflow execution.
    """

    # Document identification
    document_id: str
    job_id: str

    # Original transcription
    transcript_text: str

    # AI analysis
    document_metadata: dict[str, Any]
    segments: list[dict[str, Any]]

    # Classification batches
    batches: list[dict[str, Any]]
    current_batch_index: int
    current_batch_id: str | None

    # User review
    user_classifications: list[dict[str, Any]]
    review_feedback: str | None

    # Workflow control
    current_mode: Literal[
        "ANALYZE",
        "PRESENT_BATCH",
        "PROCESS_BATCH_RESPONSE",
        "REVISE_DOCUMENT",
        "FINALIZE_DOCUMENT",
    ]

    document_status: str
    error: str | None
