from typing import Literal

from pydantic import BaseModel


class JobCreate(BaseModel):
    source_type: Literal["upload", "microphone"] = "upload"