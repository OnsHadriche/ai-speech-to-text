import { useCallback, useState } from "react";
import { uploadAudio } from "../services/jobs";
import type { AudioSourceType, JobResponse } from "../services/jobs";

interface UseAudioUploadOptions {
  isBackendOnline: boolean | null;
  onSuccess?: (job: JobResponse) => void;
  onError?: (message: string) => void;
}

export function useAudioUpload({
  isBackendOnline,
  onSuccess,
  onError,
}: UseAudioUploadOptions) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);

  const upload = useCallback(
    async (file: File, sourceType: AudioSourceType) => {
      if (!file) {
        const message = "Please select or record an audio file first.";

        setError(message);
        onError?.(message);

        return null;
      }

      if (isBackendOnline !== true) {
        const message =
          "The backend server is unavailable. Please check that the backend is running.";

        setError(message);
        onError?.(message);

        return null;
      }

      try {
        setIsUploading(true);
        setError(null);

        const uploadedJob = await uploadAudio(file, sourceType);

        setJob(uploadedJob);
        onSuccess?.(uploadedJob);

        return uploadedJob;
      } catch (uploadError) {
        const message =
          uploadError instanceof Error
            ? uploadError.message
            : "Failed to upload audio.";

        setError(message);
        onError?.(message);

        return null;
      } finally {
        setIsUploading(false);
      }
    },
    [isBackendOnline, onSuccess, onError]
  );

  const reset = useCallback(() => {
    setJob(null);
    setError(null);
    setIsUploading(false);
  }, []);

  return {
    upload,
    job,
    error,
    isUploading,
    reset,
  };
}