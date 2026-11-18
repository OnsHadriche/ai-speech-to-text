from app.schemas.job import  JobResponse,JobCreate
from app.schemas.transcription import TranscriptionResponse,TranscriptionFailureRequest
from app.schemas.document import DocumentCreate,DocumentResponse
from app.schemas.segment import SegmentClassificationRequest, SegmentUpdateRequest, SegmentResponse
from app.schemas.revision import RevisionCreate,RevisionResponse
from app.schemas.batch import BatchClassificationRequest, BatchCreate,BatchResponse, BatchSubmissionRequest
__all__=["JobCreate","JobResponse","TranscriptionResponse","TranscriptionFailureRequest","DocumentCreate","DocumentResponse","SegmentClassificationRequest","SegmentUpdateRequest","SegmentResponse","RevisionCreate","RevisionResponse","BatchClassificationRequest","BatchCreate","BatchResponse","BatchSubmissionRequest"]