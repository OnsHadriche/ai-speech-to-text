
import json

from groq import Groq

from app.schemas.ai_analysis import DocumentAnalysisResponse
from ai.groq_client import get_groq_client, get_groq_model
from ai.prompts import ARABIC_EDUCATIONAL_ANALYSIS_PROMPT


def validate_transcript_preservation(
    transcript: str,
    analysis: DocumentAnalysisResponse,
) -> None:
    """
    Ensure that AI segmentation preserves the exact transcript.

    No normalization is performed: spaces, punctuation and newlines
    must remain unchanged.
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
        analysis = DocumentAnalysisResponse.model_validate(parsed_response)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            "Groq returned an invalid educational analysis."
        ) from exc

    validate_transcript_preservation(transcript, analysis)

    return analysis
