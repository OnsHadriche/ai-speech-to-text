from types import SimpleNamespace

import pytest

from ai.analysis_service import validate_transcript_preservation


def make_analysis(*texts):
    segments = [
        SimpleNamespace(original_text=text)
        for text in texts
    ]

    return SimpleNamespace(segments=segments)

def test_preserves_exact_transcript():
    transcript = "Introduction. Definition. Example."

    analysis = make_analysis(
        "Introduction. ",
        "Definition. ",
        "Example.",
    )

    validate_transcript_preservation(transcript, analysis)

def test_rejects_missing_text():
    transcript = "Introduction. Definition. Example."

    analysis = make_analysis(
        "Introduction.",
        "Example.",
    )

    with pytest.raises(ValueError):
        validate_transcript_preservation(transcript, analysis)


def test_rejects_rewritten_text():
    transcript = "The system is important."

    analysis = make_analysis(
        "The system is very important.",
    )

    with pytest.raises(ValueError):
        validate_transcript_preservation(transcript, analysis)


def test_rejects_reordered_text():
    transcript = "First sentence. Second sentence."

    analysis = make_analysis(
        "Second sentence.",
        "First sentence.",
    )

    with pytest.raises(ValueError):
        validate_transcript_preservation(transcript, analysis)


def test_rejects_added_text():
    transcript = "Original text."

    analysis = make_analysis(
        "Original text.",
        "AI-generated addition.",
    )

    with pytest.raises(ValueError):
        validate_transcript_preservation(transcript, analysis)