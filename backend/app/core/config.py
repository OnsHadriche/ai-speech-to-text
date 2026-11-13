from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_env: str = "development"

    database_url: str

    max_upload_size_mb: int = 100

    storage_dir: Path = PROJECT_ROOT / "storage"
    max_transcription_attempts: int = 3

    n8n_webhook_url: str | None = None
    recovery_api_key: str | None = None
    allowed_audio_extensions: set[str] = {
        ".wav",
        ".mp3",
        ".m4a",
        ".mp4",
        ".webm",
        ".ogg",
        ".flac",
    }
    target_sample_rate: int = 16000
    supported_extensions: set[str] = {
        ".wav",
        ".mp3",
        ".m4a",
        ".webm",
        ".ogg",
        ".flac",
    }
    
    upload_chunk_size: int = 1024 * 1024
    

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )


settings = Settings()
# Create storage directories automatically

STORAGE_DIRECTORIES = [
    settings.storage_dir / "audio" / "originals",
    settings.storage_dir / "audio" / "processed",
    settings.storage_dir / "documents",
    settings.storage_dir / "transcripts",
    settings.storage_dir / "models",
    settings.storage_dir / "watermarks",
    settings.storage_dir / "temp",
]

for directory in STORAGE_DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)