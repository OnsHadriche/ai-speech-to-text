const API_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// --------------------------------------------------
// Types
// --------------------------------------------------

export interface CreateDocumentRequest {
  job_id: string;
  language: string;
  reviewed_transcript: string;
}

export interface DocumentResponse {
  id: string;
  job_id: string;
  title: string | null;
  subject: string | null;
  topic: string | null;
  document_type: string | null;
  language: string;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface AnalyzeDocumentResponse {
  message: string;
  document: {
    id: string;
    title: string | null;
    subject: string | null;
    topic: string | null;
    document_type: string | null;
    language: string;
    status: string;
  };
  total_segments: number;
  total_batches: number;
  batches: {
    id: string;
    batch_number: number;
    status: string;
  }[];
}

// --------------------------------------------------
// API error handling
// --------------------------------------------------

async function handleApiError(
  response: Response
): Promise<never> {
  let message = "Request failed.";

  try {
    const errorData = await response.json();

    message =
      errorData.detail ??
      errorData.message ??
      message;
  } catch {
    // Use default error message
  }

  throw new Error(message);
}

// --------------------------------------------------
// Create document
// --------------------------------------------------

export async function createDocument(
  payload: CreateDocumentRequest
): Promise<DocumentResponse> {
  const response = await fetch(`${API_URL}/api/documents/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  return response.json();
}

// --------------------------------------------------
// Analyze document
// --------------------------------------------------

export async function analyzeDocument(
  documentId: string,
  batchSize: number = 4
): Promise<AnalyzeDocumentResponse> {
  const response = await fetch(
    `${API_URL}/api/documents/${documentId}/analyze?batch_size=${batchSize}`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    await handleApiError(response);
  }

  return response.json();
}