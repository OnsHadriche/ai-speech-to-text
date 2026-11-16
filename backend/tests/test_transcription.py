
from pathlib import Path

import pytest

from app.services.transcription import (
    TranscriptionService,
    TranscriptionError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIO_DIR = PROJECT_ROOT / "storage" / "audio" / "processed"


@pytest.mark.integration
def test_transcription():
    audio_files = list(AUDIO_DIR.glob("*.wav"))

    if not audio_files:
        pytest.skip(
            f"No processed WAV files found in {AUDIO_DIR}"
        )

    transcription_service = TranscriptionService()

    for audio_file in audio_files:
        print(f"\nFound audio file: {audio_file.name}")
        print("Starting transcription...")

        try:
            result = transcription_service.transcribe(
                audio_path=str(audio_file)
            )

            print("\n--- TRANSCRIPTION RESULT ---")
            print(f"Language: {result.language}")
            print(
                f"Language probability: "
                f"{result.language_probability}"
            )
            print(f"Duration: {result.duration_seconds}s")

            print("\nTranscribed text:")
            print(result.text)

            print("\nSegments:")
            for segment in result.segments:
                print(
                    f"[{segment.start:.2f}s - "
                    f"{segment.end:.2f}s] "
                    f"{segment.text}"
                )

        except TranscriptionError as exc:
            pytest.fail(f"Transcription failed: {exc}")
