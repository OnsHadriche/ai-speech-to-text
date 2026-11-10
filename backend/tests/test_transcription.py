
from pathlib import Path

from app.services.transcription import (
    transcription_service,
    TranscriptionError,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

AUDIO_DIR = PROJECT_ROOT / "storage" / "audio" / "processed"


def test_transcription():
    audio_files = list(AUDIO_DIR.glob("*.wav"))

    if not audio_files:
        raise FileNotFoundError(
            f"No processed WAV files found in {AUDIO_DIR}"
        )
    for audio_file in audio_files:
        print(f"Found audio file: {audio_file.name}")

        print("Starting transcription...")

        try:
            result = transcription_service.transcribe(audio_file)

            print("\n--- TRANSCRIPTION RESULT ---")
            print(f"Language: {result.language}")
            print(f"Language probability: {result.language_probability}")
            print(f"Duration: {result.duration_seconds}s")

            print("\nTranscribed text:")
            print(result.text)

            print("\nSegments:")
            for segment in result.segments:
                print(
                    f"[{segment.start:.2f}s - {segment.end:.2f}s] "
                    f"{segment.text}"
                )

        except TranscriptionError as exc:
            print(f"Transcription failed: {exc}")
            raise


if __name__ == "__main__":
    test_transcription()
