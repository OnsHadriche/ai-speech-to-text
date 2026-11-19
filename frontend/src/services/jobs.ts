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
    let errorMessage = "Failed to upload audio.";

    try {
      const errorData = await response.json();
      errorMessage =
        errorData.detail ?? errorData.message ?? errorMessage;
    } catch {
      // Use default error message if response isn't JSON
    }

    throw new Error(errorMessage);
  }

  return response.json();
}