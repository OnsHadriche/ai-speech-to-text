
from pathlib import Path
from dataclasses import dataclass

import av
import numpy as np
import soundfile as sf
from app.core.config import settings


class AudioProcessingError(Exception):
    """Raised when an audio file cannot be validated or processed."""
    


@dataclass
class AudioMetadata:
    duration_seconds: float
    sample_rate: int
    channels: int
    codec: str
    format_name: str
    processed_path: Path


def process_audio(
    input_path: Path,
    output_path: Path,
    max_duration_seconds: int = 7200,
) -> AudioMetadata:
    """
    Validate and convert an audio file to:
    WAV / PCM 16-bit / mono / 16 kHz.

    PyAV handles the input decoding.
    SoundFile writes the normalized WAV.
    """
    # Input and output paths are converted to Path objects if they are not already.

    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Validate input file existence and extension
    if not input_path.exists() or not input_path.is_file():
        raise AudioProcessingError("Audio file does not exist.")

    if input_path.suffix.lower() not in settings.supported_extensions:
        raise AudioProcessingError("Unsupported audio extension.")

    if input_path.stat().st_size == 0:
        raise AudioProcessingError("Audio file is empty.")

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize total_samples to keep track of the number of audio samples processed
    total_samples = 0

    try:
        # Open the input audio file using PyAV
        with av.open(str(input_path), mode="r") as container:
            # Filter audio streams from the container
            audio_streams = [
                stream
                for stream in container.streams
                if stream.type == "audio"
            ]
            # Check if any audio streams are found; if not, raise an error
            if not audio_streams:
                raise AudioProcessingError(
                    "No valid audio stream found."
                )
            
            # Select the first audio stream for processing

            stream = audio_streams[0]
            # Check if the sample rate is available; if not, raise an error

            if not stream.codec_context.sample_rate:
                raise AudioProcessingError(
                    "Audio sample rate is unavailable."
                )

            original_sample_rate = stream.codec_context.sample_rate
            original_channels = (
                len(stream.codec_context.layout.channels)
                if stream.codec_context.layout
                else 0
            )
            codec = stream.codec_context.name or "unknown"
            format_name = container.format.name or "unknown"

            resampler = av.AudioResampler(
                format="s16",
                layout="mono",
                rate=settings.target_sample_rate,
            )

            with sf.SoundFile(
                str(output_path),
                mode="w",
                samplerate=settings.target_sample_rate,
                channels=1,
                subtype="PCM_16",
                format="WAV",
            ) as output:
                # Define a nested function to write resampled audio frames to the output file
                def write_resampled(frames):
                    """
                    Writes resampled audio frames to the output file.
                    frames: List of audio frames to be written.
                    output: SoundFile object for writing audio data.
                    total_samples: Counter for the total number of audio samples processed.
                    """
                    nonlocal total_samples

                    for frame in frames:
                        samples = frame.to_ndarray().reshape(-1, 1)

                        if samples.size == 0:
                            continue

                        total_samples += len(samples)

                        duration = total_samples / settings.target_sample_rate

                        if duration > max_duration_seconds:
                            raise AudioProcessingError(
                                "Audio exceeds the maximum duration."
                            )

                        output.write(samples)

                for frame in container.decode(stream):
                    write_resampled(resampler.resample(frame))

                # Flush samples buffered by the resampler.
                write_resampled(resampler.resample(None))

        if total_samples == 0:
            raise AudioProcessingError(
                "No decodable audio samples found."
            )

        duration_seconds = total_samples / settings.target_sample_rate

        return AudioMetadata(
            duration_seconds=round(duration_seconds, 3),
            sample_rate=original_sample_rate,
            channels=original_channels,
            codec=codec,
            format_name=format_name,
            processed_path=output_path,
        )

    except AudioProcessingError:
        output_path.unlink(missing_ok=True)
        raise

    except (av.error.FFmpegError, OSError, ValueError) as exc:
        output_path.unlink(missing_ok=True)

        raise AudioProcessingError(
            "The audio file is invalid or could not be decoded."
        ) from exc

    except Exception:
        output_path.unlink(missing_ok=True)
        raise
