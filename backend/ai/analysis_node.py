
from backend.ai.analysis_service import analyze_educational_transcript
from backend.ai.ai_state import EducationalAgentState


def analyze_document_node(
    state: EducationalAgentState,
) -> dict:
    """
    LangGraph node responsible for analyzing an educational transcript.

    This node does not write to PostgreSQL.
    It returns updates to the shared agent state.
    """

    transcript = state.get("transcript_text")

    if not transcript or not transcript.strip():
        raise ValueError("The agent state does not contain a valid transcript.")

    # Call Groq analysis service
    analysis = analyze_educational_transcript(transcript)

    # Extract document metadata
    document_metadata = {
        "document_title": analysis.document_title,
        "subject": analysis.subject,
        "topic": analysis.topic,
        "document_type": analysis.document_type,
    }

    # Convert Pydantic segments into dictionaries
    segments = [
        segment.model_dump()
        for segment in analysis.segments
    ]

    # Return state updates
    return {
        "document_metadata": document_metadata,
        "segments": segments,
        "current_mode": "PRESENT_BATCH",
        "document_status": "classification_in_progress",
        "error": None,
    }
