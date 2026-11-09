
from pathlib import Path

from app.services.audio_processing import (
    process_audio,
    AudioProcessingError,
)

INPUT_DIR = Path("storage/audio")
OUTPUT_DIR = Path("storage/processed")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for input_path in INPUT_DIR.iterdir():

    if input_path.suffix.lower() not in {
        ".wav", ".mp3", ".m4a", ".webm", ".ogg"
    }:
        continue

    output_path = OUTPUT_DIR / f"{input_path.stem}.wav"

    print(f"\nProcessing: {input_path.name}")

    try:
        metadata = process_audio(
            input_path=input_path,
            output_path=output_path,
        )

        print("Success")
        print(f"Duration: {metadata.duration_seconds} seconds")
        print(f"Original sample rate: {metadata.sample_rate}")
        print(f"Original channels: {metadata.channels}")
        print(f"Codec: {metadata.codec}")
        print(f"Container: {metadata.format_name}")
        print(f"Processed file: {metadata.processed_path}")

    except AudioProcessingError as exc:
        print(f"Audio validation failed: {exc}")
