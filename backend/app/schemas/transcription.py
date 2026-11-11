
from pydantic import BaseModel

class TranscriptionResponse(BaseModel):
    job_id: str
    status: str
    language: str
    language_probability: float
    duration_seconds: float
    text: str
    segments: list[dict]
class TranscriptionFailureRequest(BaseModel):
    error_message: str