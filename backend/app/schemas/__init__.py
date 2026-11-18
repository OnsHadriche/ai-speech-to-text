from app.schemas.job import  JobResponse,JobCreate
from app.schemas.transcription import TranscriptionResponse,TranscriptionFailureRequest
from app.schemas.document import DocumentCreate,DocumentResponse
from app.schemas.segment import DocumentSegmentCreate,DocumentSegmentResponse
from app.schemas.revision import DocumentRevisionCreate,DocumentRevisionResponse
from app.schemas.batch import DocumentBatchCreate,DocumentBatchResponse
__all__=["JobCreate","JobResponse","TranscriptionResponse","TranscriptionFailureRequest","DocumentSegmentCreate","DocumentSegmentResponse","DocumentRevisionCreate","DocumentRevisionResponse","DocumentBatchCreate","DocumentBatchResponse"]