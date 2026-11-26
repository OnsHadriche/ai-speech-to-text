
import type {
  StructuringRequest,
  StructuringResponse,
} from "../types/structuring";

const API_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function handleApiError(response: Response): Promise<never> {
  let message = "Failed to structure transcript.";

  try {
    const errorData = await response.json();
    message = errorData.detail ?? errorData.message ?? message;
  } catch {
    // Keep default message
  }

  throw new Error(message);
}

export async function structureTranscript(
  transcript: string
): Promise<StructuringResponse> {
  const payload: StructuringRequest = {
    transcript,
  };

  const response = await fetch(`${API_URL}/api/structuring/analyze`, {
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
