
from app.services.ai.ai_state import EducationalAgentState


def present_batch_node(
    state: EducationalAgentState,
) -> dict:
    """
    Prepare the next classification batch for user review.

    Batches must already be loaded from the database
    and supplied in the agent state.
    """

    batches = state.get("batches", [])
    current_index = state.get("current_batch_index", 0)

    if not batches:
        raise ValueError("No classification batches are available.")

    if current_index < 0:
        raise ValueError("Invalid batch index.")

    # Find the next batch that is not completed or skipped.
    while current_index < len(batches):
        batch = batches[current_index]

        if batch.get("status") not in ("completed", "skipped"):
            break

        current_index += 1

    # All batches have been reviewed.
    if current_index >= len(batches):
        return {
            "current_batch_index": current_index,
            "current_batch_id": None,
            "current_mode": "REVISE_DOCUMENT",
        }

    batch = batches[current_index]
    segments = batch.get("segments", [])

    if not segments:
        raise ValueError(
            f"Batch {current_index + 1} contains no segments."
        )

    if len(segments) > 5:
        raise ValueError(
            "A review batch cannot contain more than 5 segments."
        )

    # Prepare the user review payload.
    review_segments = [
        {
            "id": segment.get("id"),
            "position": segment.get("position"),
            "original_text": segment["original_text"],
            "suggested_type": segment.get("suggested_type"),
            "suggestion_confidence": segment.get(
                "suggestion_confidence"
            ),
            "suggestion_reason": segment.get("suggestion_reason"),
            "selected_type": None,
            "classification_status": "awaiting_confirmation",
        }
        for segment in segments
    ]

    return {
        "current_batch_index": current_index,
        "current_batch_id": batch.get("id"),
        "current_mode": "PRESENT_BATCH",
        "document_status": "classification_in_progress",
        "user_classifications": [],
        "review_segments": review_segments,
    }
