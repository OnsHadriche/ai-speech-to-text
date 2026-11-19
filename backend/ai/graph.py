
from langgraph.graph import StateGraph, START, END

from ai.ai_state import EducationalAgentState
from ai.analysis_node import analyze_document_node
from ai.presentation_node import present_batch_node
from ai.batch_response_node import (
    process_batch_response_node,
)
from ai.revision_node import revise_document_node
from ai.finalization_node import finalize_document_node


def route_agent(state: EducationalAgentState) -> str:
    """Choose the operation based on the current agent mode."""

    mode = state.get("current_mode")

    routes = {
        "ANALYZE": "analyze",
        "PRESENT_BATCH": "present_batch",
        "PROCESS_BATCH_RESPONSE": "process_batch_response",
        "REVISE_DOCUMENT": "revise_document",
        "FINALIZE_DOCUMENT": "finalize_document",
    }

    if mode not in routes:
        raise ValueError(f"Unsupported agent mode: {mode}")

    return routes[mode]


def build_educational_agent():
    """Build and compile the educational document workflow."""

    workflow = StateGraph(EducationalAgentState)

    # Register nodes
    workflow.add_node("analyze", analyze_document_node)
    workflow.add_node("present_batch", present_batch_node)
    workflow.add_node(
        "process_batch_response",
        process_batch_response_node,
    )
    workflow.add_node("revise_document", revise_document_node)
    workflow.add_node("finalize_document", finalize_document_node)

    # Select the node when execution starts
    workflow.add_conditional_edges(
        START,
        route_agent,
        {
            "analyze": "analyze",
            "present_batch": "present_batch",
            "process_batch_response": "process_batch_response",
            "revise_document": "revise_document",
            "finalize_document": "finalize_document",
        },
    )

    # Return control to the caller after one operation.
    workflow.add_edge("analyze", END)
    workflow.add_edge("present_batch", END)
    workflow.add_edge("process_batch_response", END)
    workflow.add_edge("revise_document", END)
    workflow.add_edge("finalize_document", END)

    return workflow.compile()


educational_agent = build_educational_agent()
