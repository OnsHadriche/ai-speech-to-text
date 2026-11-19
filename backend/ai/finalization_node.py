
from backend.ai.ai_state import EducationalAgentState


def finalize_document_node(
    state: EducationalAgentState,
) -> dict:
    """
    Validate the database finalization result.

    The database validation itself is performed by:
    document_validation_service.finalize_document()

    This node processes its result and updates the agent state.
    """

    result = state.get("finalization_result")

    if not result:
        raise ValueError(
            "Missing document finalization result."
        )

    if not result.get("is_valid", False):
        errors = result.get("errors", [])

        return {
            "document_status": "review_required",
            "current_mode": "REVISE_DOCUMENT",
            "error": "; ".join(errors) if errors else (
                "Document validation failed."
            ),
        }

    total_segments = result.get("total_segments", 0)
    confirmed_segments = result.get("confirmed_segments", 0)

    if total_segments <= 0:
        raise ValueError("The document contains no segments.")

    if confirmed_segments != total_segments:
        raise ValueError(
            "Not all segments have been confirmed by the user."
        )

    return {
        "document_status": "ready_for_generation",
        "current_mode": "FINALIZE_DOCUMENT",
        "error": None,
    }
