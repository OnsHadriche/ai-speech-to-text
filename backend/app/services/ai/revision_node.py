
from app.services.ai.ai_state import EducationalAgentState


ALLOWED_REVISION_ACTIONS = {
    "classification_changed",
    "text_corrected",
    "segment_created",
    "segment_deleted",
    "segment_split",
    "segments_merged",
    "segment_reordered",
    "parent_changed",
}


def revise_document_node(
    state: EducationalAgentState,
) -> dict:
    """
    Validate user-requested document revisions.

    Actual database modifications are delegated to the existing
    structure_service and classification_service.

    This node never modifies the database directly.
    """

    revision_requests = state.get("revision_requests", [])

    if not revision_requests:
        return {
            "current_mode": "FINALIZE_DOCUMENT",
            "error": None,
        }

    validated_requests = []

    for index, request in enumerate(revision_requests, start=1):

        action = request.get("action")
        segment_id = request.get("segment_id")

        if action not in ALLOWED_REVISION_ACTIONS:
            raise ValueError(
                f"Revision {index}: unsupported action '{action}'."
            )

        if not segment_id:
            raise ValueError(
                f"Revision {index}: segment_id is required."
            )

        validated_requests.append({
            **request,
            "status": "pending",
        })

    return {
        "revision_requests": validated_requests,
        "current_mode": "REVISE_DOCUMENT",
        "document_status": "review_required",
        "error": None,
    }
