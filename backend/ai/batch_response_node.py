
from backend.ai.ai_state import EducationalAgentState


ALLOWED_SEGMENT_TYPES = {
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
}


def process_batch_response_node(
    state: EducationalAgentState,
) -> dict:
    """
    Validate user classifications for the current review batch.

    Database persistence is handled separately by classification_service.
    """

    review_segments = state.get("review_segments", [])
    user_classifications = state.get("user_classifications", [])
    current_batch_id = state.get("current_batch_id")

    if not current_batch_id:
        raise ValueError("No active review batch.")

    if not review_segments:
        raise ValueError("No segments are available for review.")

    if not user_classifications:
        raise ValueError("No user classifications were submitted.")

    expected_ids = {
        segment.get("id")
        for segment in review_segments
    }

    submitted_ids = set()
    validated_classifications = []

    for classification in user_classifications:
        segment_id = classification.get("segment_id")
        selected_type = classification.get("selected_type")

        if not segment_id or segment_id not in expected_ids:
            raise ValueError(
                f"Invalid segment ID: {segment_id}"
            )

        if segment_id in submitted_ids:
            raise ValueError(
                f"Duplicate classification for segment: {segment_id}"
            )

        if selected_type not in ALLOWED_SEGMENT_TYPES:
            raise ValueError(
                f"Invalid segment type: {selected_type}"
            )

        submitted_ids.add(segment_id)

        validated_classifications.append({
            "segment_id": segment_id,
            "selected_type": selected_type,
            "classification_source": "user",
            "classification_status": "confirmed",
        })

    # Require a decision for every segment in the batch.
    missing_ids = expected_ids - submitted_ids

    if missing_ids:
        raise ValueError(
            f"Missing classifications for {len(missing_ids)} segments."
        )

    # Move to the next batch.
    next_batch_index = state.get("current_batch_index", 0) + 1

    return {
        "user_classifications": validated_classifications,
        "current_batch_index": next_batch_index,
        "current_batch_id": None,
        "review_segments": [],
        "current_mode": "PRESENT_BATCH",
        "error": None,
    }
