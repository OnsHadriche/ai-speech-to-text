
from unittest.mock import patch

from app.schemas.ai_analysis import DocumentAnalysisResponse
from backend.ai.graph import build_educational_agent


def test_complete_educational_agent_workflow():

    transcript = (
        "الدرس الأول\n"
        "تعريف البرمجة\n"
        "البرمجة هي كتابة التعليمات للحاسوب.\n"
        "مثال: استعمال لغة Python."
    )

    # Simulated Groq response
    mock_analysis = DocumentAnalysisResponse(
        document_title="مقدمة في البرمجة",
        subject="الإعلامية",
        topic="البرمجة",
        document_type="lesson",
        segments=[
            {
                "original_text": "الدرس الأول\n",
                "suggested_type": "title",
                "suggestion_confidence": 0.99,
                "suggestion_reason": "عنوان الدرس",
            },
            {
                "original_text": "تعريف البرمجة\n",
                "suggested_type": "heading",
                "suggestion_confidence": 0.95,
                "suggestion_reason": "عنوان فرعي",
            },
            {
                "original_text": "البرمجة هي كتابة التعليمات للحاسوب.\n",
                "suggested_type": "definition",
                "suggestion_confidence": 0.98,
                "suggestion_reason": "تعريف البرمجة",
            },
            {
                "original_text": "مثال: استعمال لغة Python.",
                "suggested_type": "example",
                "suggestion_confidence": 0.97,
                "suggestion_reason": "مثال تطبيقي",
            },
        ],
    )

    # Patch the Groq operation before building the graph.
    with patch(
        "app.services.ai.analysis_node.analyze_educational_transcript",
        return_value=mock_analysis,
    ):

        agent = build_educational_agent()

        # ---------------------------------
        # 1. ANALYZE
        # ---------------------------------

        state = agent.invoke({
            "document_id": "test-document",
            "transcript_text": transcript,
            "current_mode": "ANALYZE",
        })

        assert state["current_mode"] == "PRESENT_BATCH"
        assert len(state["segments"]) == 4

        print("1. ANALYZE: PASSED")

        # ---------------------------------
        # Prepare a simulated review batch
        # ---------------------------------

        segments = []

        for index, segment in enumerate(state["segments"], start=1):
            segments.append({
                **segment,
                "id": f"segment-{index}",
                "position": index,
            })

        state["batches"] = [
            {
                "id": "batch-1",
                "status": "presented",
                "segments": segments,
            }
        ]

        state["current_batch_index"] = 0

        # ---------------------------------
        # 2. PRESENT_BATCH
        # ---------------------------------

        state = agent.invoke(state)

        assert state["current_mode"] == "PRESENT_BATCH"
        assert state["current_batch_id"] == "batch-1"
        assert len(state["review_segments"]) == 4

        print("2. PRESENT_BATCH: PASSED")

        # ---------------------------------
        # 3. PROCESS_BATCH_RESPONSE
        # ---------------------------------

        state["current_mode"] = "PROCESS_BATCH_RESPONSE"

        state["user_classifications"] = [
            {
                "segment_id": "segment-1",
                "selected_type": "title",
            },
            {
                "segment_id": "segment-2",
                "selected_type": "heading",
            },
            {
                "segment_id": "segment-3",
                "selected_type": "definition",
            },
            {
                "segment_id": "segment-4",
                "selected_type": "example",
            },
        ]

        state = agent.invoke(state)

        assert state["current_mode"] == "PRESENT_BATCH"
        assert len(state["user_classifications"]) == 4

        print("3. PROCESS_BATCH_RESPONSE: PASSED")

        # ---------------------------------
        # 4. REVISE_DOCUMENT
        # ---------------------------------

        state["current_mode"] = "REVISE_DOCUMENT"
        state["revision_requests"] = []

        state = agent.invoke(state)

        assert state["current_mode"] == "FINALIZE_DOCUMENT"

        print("4. REVISE_DOCUMENT: PASSED")

        # ---------------------------------
        # 5. FINALIZE_DOCUMENT
        # ---------------------------------

        state["finalization_result"] = {
            "is_valid": True,
            "total_segments": 4,
            "confirmed_segments": 4,
            "errors": [],
        }

        state = agent.invoke(state)

        assert state["document_status"] == "ready_for_generation"

        print("5. FINALIZE_DOCUMENT: PASSED")

        print("\nComplete LangGraph workflow: PASSED")


def test_agent_rejects_invalid_mode():

    agent = build_educational_agent()

    try:
        agent.invoke({
            "current_mode": "INVALID_MODE",
        })
    except ValueError:
        print("Invalid mode rejection: PASSED")
    else:
        raise AssertionError("Invalid mode was not rejected.")
