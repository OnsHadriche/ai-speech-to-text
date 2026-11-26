
import json

from groq import Groq

from app.schemas.ai_analysis import DocumentAnalysisResponse
from ai.groq_client import get_groq_client, get_groq_model
from ai.prompts import ARABIC_EDUCATIONAL_ANALYSIS_PROMPT


STRUCTURAL_SEGMENT_TYPES = {
    "title",
    "subtitle",
    "heading",
    "subheading",
}


def validate_transcript_preservation(
    transcript: str,
    analysis: DocumentAnalysisResponse,
) -> None:
    """
    Ensure AI segmentation preserves the exact transcript.

    No normalization is performed. Spaces, punctuation,
    and newlines must remain unchanged.
    """

    reconstructed_text = "".join(
        segment.original_text
        for segment in analysis.segments
    )

    if reconstructed_text != transcript:
        raise ValueError(
            "AI analysis failed transcript preservation validation. "
            "The segments do not reproduce the original transcription."
        )


def validate_segment_hierarchy(
    analysis: DocumentAnalysisResponse,
) -> None:
    """
    Validate hierarchical relationships between AI segments.

    Rules:
    - Top-level segments must have parent_segment_index=None.
    - Parent indices must reference an existing segment.
    - Parents must appear before their children.
    - A segment cannot be its own parent.
    - Parents must be structural segments.
    """

    segments = analysis.segments

    for child_index, segment in enumerate(segments):
        parent_index = segment.parent_segment_index

        # Top-level segment
        if parent_index is None:
            continue
        if not isinstance(parent_index, int) or isinstance(parent_index, bool):
            raise ValueError(
                f"Invalid parent index for segment {child_index}: "
                f"{parent_index}"
            )
        # Reject invalid index values
        if parent_index < 0 or parent_index >= len(segments):
            raise ValueError(
                f"Segment {child_index} has invalid parent index "
                f"{parent_index}."
            )

        # Reject self-parent relationships
        if parent_index == child_index:
            raise ValueError(
                f"Segment {child_index} cannot be its own parent."
            )

        # Parent must precede child
        if parent_index >= child_index:
            raise ValueError(
                f"Segment {child_index} references parent "
                f"{parent_index}, but parents must appear earlier."
            )

        parent_segment = segments[parent_index]

        # Only structural segments may be parents
        if parent_segment.suggested_type not in STRUCTURAL_SEGMENT_TYPES:
            raise ValueError(
                f"Segment {child_index} references segment "
                f"{parent_index} as parent, but the parent is not "
                "a structural segment."
            )


def validate_analysis(
    transcript: str,
    analysis: DocumentAnalysisResponse,
) -> None:
    """
    Validate the complete AI analysis before returning it.
    """

    validate_transcript_preservation(
        transcript=transcript,
        analysis=analysis,
    )

    validate_segment_hierarchy(
        analysis=analysis,
    )


def analyze_educational_transcript(
    transcript: str,
) -> DocumentAnalysisResponse:
    """
    Analyze an Arabic educational transcript using Groq.

    Returns validated educational metadata and segments.
    Does not save anything to the database.
    """

    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("Transcript cannot be empty.")

    client: Groq = get_groq_client()
    model = get_groq_model()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": ARABIC_EDUCATIONAL_ANALYSIS_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "Analyze the following transcription.\n\n"
                    "TRANSCRIPTION:\n"
                    f"{transcript}"
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "educational_document_analysis",
                "strict": True,
                "schema": DocumentAnalysisResponse.model_json_schema(),
            },
        },
        temperature=0,
    )

    if not response.choices:
        raise RuntimeError("Groq returned an empty response.")

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("Groq returned an empty analysis.")

    try:
        parsed_response = json.loads(content)

        analysis = DocumentAnalysisResponse.model_validate(
            parsed_response
        )

    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            "Groq returned an invalid educational analysis."
        ) from exc

    try:
        validate_analysis(
            transcript=transcript,
            analysis=analysis,
        )

    except ValueError as exc:
        raise RuntimeError(
            f"AI analysis validation failed: {exc}"
        ) from exc

    return analysis
