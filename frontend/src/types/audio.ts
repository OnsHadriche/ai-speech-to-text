import type { AudioSourceType, JobResponse } from "../services/jobs";

export type { AudioSourceType, JobResponse };

export interface SelectedAudio {
  file: File;
  sourceType: AudioSourceType;
}

export interface UploadState {
  isUploading: boolean;
  error: string | null;
  job: JobResponse | null;
}