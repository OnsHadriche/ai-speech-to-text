
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field


class JobResponse(BaseModel):
    id: str
    original_name: str
    stored_filename: str
    content_type: str
    size_byte: int
    storage_path: str
    source_type: str
    duration_seconds: float | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def file_extension(self) -> str:
        from pathlib import Path
        return Path(self.original_name).suffix.lower()
