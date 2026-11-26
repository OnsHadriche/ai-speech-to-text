
import { useState } from "react";
import { FileText, RotateCcw } from "lucide-react";

import type { JobResponse } from "../../services/jobs";
import useJobPolling from "../../hooks/useJobPolling";

import Button from "../ui/Button";
import TranscriptionLoadingState from "./TranscriptionLoadingState";
import TranscriptionError from "./TranscriptionError";
import TranscriptionSummary from "./TranscriptionSummary";
import TranscriptEditor from "./TranscriptEditor";
import NextStepCard from "./NextStepCard";

interface TranscriptionPanelProps {
  job: JobResponse;
  onStartNewDocument: () => void;
}

export default function TranscriptionPanel({
  job,
  onStartNewDocument,
}: TranscriptionPanelProps) {
  // 1. Poll backend for the latest job status
  const {
    job: currentJob,
    error: pollingError,
  } = useJobPolling({
    jobId: job.id,
    enabled: true,
    interval: 2000,
  });

  // 2. Store only the user's edits
  const [transcriptEdit, setTranscriptEdit] = useState<{
    jobId: JobResponse["id"];
    text: string;
  } | null>(null);

  // 3. Get the transcript:
  //    - User's edited version if available
  //    - Otherwise the backend transcript
  const transcriptText =
    transcriptEdit?.jobId === job.id
      ? transcriptEdit.text
      : currentJob?.transcript_text ?? job.transcript_text ?? "";

  // 4. Calculate word count
  const wordCount = transcriptText
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;

  // 5. Determine job state
  const isWaiting = currentJob?.status === "audio_processed";

  const isTranscribing = currentJob?.status === "transcribing";

  const isProcessing = isWaiting || isTranscribing;

  const isCompleted = currentJob?.status === "transcribed";

  const isFailed =
    currentJob?.status === "transcription_failed" ||
    currentJob?.status === "failed_permanently";

  // 6. Determine error message
  const errorMessage =
    currentJob?.error_message ??
    pollingError ??
    "An unexpected error occurred during transcription.";

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <FileText size={22} className="text-violet-600" />

            <h2 className="text-xl font-semibold text-slate-900">
              Transcription
            </h2>
          </div>

          <p className="mt-1 text-sm text-slate-500">
            Convert your audio into editable text.
          </p>
        </div>

        <Button
          variant="secondary"
          onClick={onStartNewDocument}
          icon={<RotateCcw size={16} />}
        >
          Start New Document
        </Button>
      </div>

      {/* Audio information */}
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-100">
            <FileText size={20} className="text-violet-600" />
          </div>

          <div className="min-w-0 flex-1">
            <p className="truncate font-medium text-slate-900">
              {job.original_name}
            </p>

            <p className="text-sm text-slate-500">
              Audio successfully uploaded
            </p>
          </div>
        </div>
      </div>

      {/* Processing state */}
      {isProcessing && <TranscriptionLoadingState />}

      {/* Polling error */}
      {pollingError && !isCompleted && !isFailed && (
        <TranscriptionError message={pollingError} />
      )}

      {/* Transcription error */}
      {isFailed && <TranscriptionError message={errorMessage} />}

      {/* Completed state */}
      {isCompleted && currentJob && (
        <div className="space-y-5">
          <TranscriptionSummary
            language={currentJob.detected_language}
            duration={currentJob.duration_seconds}
            wordCount={wordCount}
          />

          <TranscriptEditor
            transcript={transcriptText}
            onTranscriptChange={(text) =>
              setTranscriptEdit({
                jobId: job.id,
                text,
              })
            }
            wordCount={wordCount}
          />

          <NextStepCard />
        </div>
      )}

      {/* Status fallback */}
      {!isProcessing && !isCompleted && !isFailed && !pollingError && (
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <p className="text-sm text-slate-500">
            Current status:
            <span className="ml-2 font-medium text-slate-700">
              {currentJob?.status ?? job.status}
            </span>
          </p>
        </div>
      )}
    </section>
  );
}
