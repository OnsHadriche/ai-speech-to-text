
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel


MODEL_SIZE = "small"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

SUPPORTED_LANGUAGES = {
    "fr": "French",
    "en": "English",
    "ar": "Arabic",
}


class TranscriptionError(Exception):
    """Raised when audio transcription fails."""


@dataclass
class TranscriptionSegment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    text: str
    language: str
    language_probability: float
    duration_seconds: float
    segments: list[TranscriptionSegment]


class TranscriptionService:

    def __init__(self):
        self.model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
        )

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        audio_path = Path(audio_path)

        if not audio_path.exists() or not audio_path.is_file():
            raise TranscriptionError("Processed audio file not found.")

        try:
            segments_generator, info = self.model.transcribe(
                str(audio_path),
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=True,
            )

            detected_language = info.language

            if detected_language not in SUPPORTED_LANGUAGES:
                raise TranscriptionError(
                    f"Unsupported language detected: {detected_language}"
                )

            segments = []
            text_parts = []

            for segment in segments_generator:
                segment_text = segment.text.strip()

                if not segment_text:
                    continue

                segments.append(
                    TranscriptionSegment(
                        start=round(segment.start, 3),
                        end=round(segment.end, 3),
                        text=segment_text,
                    )
                )

                text_parts.append(segment_text)

            if not text_parts:
                raise TranscriptionError(
                    "No speech could be detected in the audio."
                )

            return TranscriptionResult(
                text=" ".join(text_parts),
                language=detected_language,
                language_probability=round(
                    info.language_probability, 4
                ),
                duration_seconds=round(info.duration, 3),
                segments=segments,
            )

        except TranscriptionError:
            raise

        except Exception as exc:
            raise TranscriptionError(
                "Audio transcription failed."
            ) from exc



