
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type AudioSourceType = "upload" | "microphone";

export interface JobResponse {
  id: string;
  original_name: string;
  stored_filename: string;
  content_type: string;
  size_byte: number;
  storage_path: string;
  source_type: AudioSourceType;
  duration_seconds: number | null;
  
  transcript_text: string | null;
  detected_language: string | null;
  language_probability: number | null;
  transcription_segments: Record<string, unknown>[] | null;
  
  status: string;
  error_message: string | null;

  created_at: string;
  updated_at: string | null;
}

async function handleApiError(response: Response): Promise<never> {
  let errorMessage = "An unexpected error occurred.";

  try {
    const errorData = await response.json();

    errorMessage =
      errorData.detail ?? errorData.message ?? errorMessage;
  } catch {
    // Keep default error message
  }

  throw new Error(errorMessage);
}

// Upload audio
export async function uploadAudio(
  file: File,
  sourceType: AudioSourceType,
): Promise<JobResponse> {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("source_type", sourceType);

  const response = await fetch(`${API_URL}/api/jobs/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  return response.json();
}

// Transcribe uploaded audio
export async function getJob(
  jobId: string,
): Promise<JobResponse> {
  const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
    method: "GET",
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  return response.json();
}
