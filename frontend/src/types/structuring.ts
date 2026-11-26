
export interface DocumentSubsection {
  id: string;
  title: string;
  content: string;
}

export interface DocumentSection {
  id: string;
  title: string;
  content: string;
  subsections: DocumentSubsection[];
}

export interface StructuredDocument {
  document_title: string;
  summary: string;
  sections: DocumentSection[];
}

export interface StructuringRequest {
  transcript: string;
}

export interface StructuringResponse {
  document: StructuredDocument;
}
