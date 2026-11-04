from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent[3]
class Settings(BaseSettings):

    app_env: str = "development"

    database_url: str

    max_upload_size_mb: int = 100
    
    storage_path: str = PROJECT_ROOT /"storage"
    n8n_webhook_url: str | None = None
    

    model_config = SettingsConfigDict(
        env_file="../.env",
        extra="ignore"
    )


settings = Settings()