import { useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Languages,
  RotateCcw,
  Sparkles,
} from "lucide-react";

import { transcribeAudio } from "../../services/jobs";
import type { JobResponse } from "../../services/jobs";

import Button from "../ui/Button";
import LoadingSpinner from "../ui/LoadingSpinner";

interface TranscriptionPanelProps {
  job: JobResponse;
  onStartNew: () => void;
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "--:--";

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
}

export default function TranscriptionPanel({
  job,
  onStartNew,
}: TranscriptionPanelProps) {
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcriptionError, setTranscriptionError] = useState("");
  const [transcribedJob, setTranscribedJob] =
    useState<JobResponse | null>(null);
  const [transcriptText, setTranscriptText] = useState("");

  async function handleTranscribe() {
    try {
      setIsTranscribing(true);
      setTranscriptionError("");
      setTranscribedJob(null);
      setTranscriptText("");

      const result = await transcribeAudio(job.id);

      setTranscribedJob(result);
      setTranscriptText(result.transcript_text ?? "");
    } catch (error) {
      console.error("Transcription error:", error);

      setTranscriptionError(
        error instanceof Error
          ? error.message
          : "An error occurred during transcription.",
      );
    } finally {
      setIsTranscribing(false);
    }
  }

  const wordCount = transcriptText.trim()
    ? transcriptText.trim().split(/\s+/).length
    : 0;

  return (
    <div className="space-y-6">
      {/* Upload success and transcription action */}
      {!transcribedJob && (
        <section className="rounded-2xl border border-violet-200 bg-gradient-to-br from-violet-50/80 to-blue-50/80 p-6">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-violet-600 shadow-sm">
              <FileText size={21} />
            </div>

            <div className="min-w-0 flex-1">
              <h3 className="font-semibold text-slate-900">
                Audio uploaded successfully
              </h3>

              <p className="mt-1 text-sm leading-6 text-slate-500">
                Your audio is ready for transcription using the local
                speech recognition system.
              </p>

              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-lg border border-white bg-white/80 px-3 py-2 text-xs text-slate-600">
                  {job.original_name}
                </span>

                <span className="rounded-lg border border-white bg-white/80 px-3 py-2 text-xs text-emerald-700">
                  Upload completed
                </span>
              </div>
            </div>
          </div>

          {/* Transcription action */}
          <div className="mt-6">
            <Button
              disabled={isTranscribing}
              onClick={handleTranscribe}
              icon={<FileText size={17} />}
            >
              {isTranscribing ? "Transcribing..." : "Start transcription"}
            </Button>
          </div>

          {/* Transcription loading state */}
          {isTranscribing && (
            <div className="mt-5 rounded-xl border border-violet-100 bg-white/70 p-5">
              <div className="flex flex-col items-center gap-4 text-center">
                <LoadingSpinner
                  size={32}
                  text="Transcribing your audio..."
                  className="flex-col"
                />

                <div>
                  <p className="font-medium text-violet-900">
                    Transcription in progress
                  </p>

                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    Processing your audio. This may take a few moments
                    depending on its duration.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Transcription error */}
          {transcriptionError && (
            <div className="mt-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />

              <div>
                <p className="font-semibold">Transcription failed</p>
                <p className="mt-1">{transcriptionError}</p>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Transcription result */}
      {transcribedJob && (
        <div className="space-y-5">
          {/* Success summary */}
          <section className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-emerald-600 shadow-sm">
                <CheckCircle2 size={20} />
              </div>

              <div className="flex-1">
                <h3 className="font-semibold text-emerald-900">
                  Transcription completed successfully
                </h3>

                <p className="mt-1 text-sm leading-6 text-emerald-700">
                  Your audio has been converted to text. Review and
                  correct the transcript before continuing.
                </p>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {transcribedJob.detected_language && (
                <div className="flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-sm text-slate-600">
                  <Languages size={15} className="text-violet-500" />
                  Language: <strong>{transcribedJob.detected_language}</strong>
                </div>
              )}

              {transcribedJob.duration_seconds !== null && (
                <div className="rounded-lg bg-white px-3 py-2 text-sm text-slate-600">
                  Duration:{" "}
                  <strong>
                    {formatDuration(transcribedJob.duration_seconds)}
                  </strong>
                </div>
              )}

              <div className="rounded-lg bg-white px-3 py-2 text-sm text-slate-600">
                Words: <strong>{wordCount}</strong>
              </div>
            </div>
          </section>

          {/* Transcript editor */}
          <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
                  <FileText size={18} />
                </div>

                <div>
                  <h3 className="font-semibold text-slate-900">
                    Transcript review
                  </h3>

                  <p className="text-xs text-slate-500">
                    Review and edit your transcript
                  </p>
                </div>
              </div>

              <span className="rounded-full bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-700">
                {wordCount} words
              </span>
            </div>

            <div className="p-5">
              <textarea
                value={transcriptText}
                onChange={(event) => setTranscriptText(event.target.value)}
                rows={14}
                spellCheck
                placeholder="Your transcription will appear here..."
                className="w-full resize-y rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-7 text-slate-700 outline-none transition focus:border-violet-400 focus:bg-white focus:ring-4 focus:ring-violet-100"
              />

              <div className="mt-3 flex items-center justify-between gap-3">
                <p className="text-xs text-slate-400">
                  Changes are currently local to this page.
                </p>

                <span className="text-xs text-slate-400">
                  {transcriptText.length} characters
                </span>
              </div>
            </div>
          </section>

          {/* Next step */}
          <section className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50/70 to-violet-50/70 p-5">
            <div className="flex items-start gap-3">
              <Sparkles size={20} className="mt-1 text-violet-600" />

              <div>
                <h3 className="font-semibold text-slate-900">
                  Next: Structure with AI
                </h3>

                <p className="mt-1 text-sm leading-6 text-slate-500">
                  The next phase will analyze the reviewed transcript
                  and identify headings, definitions, examples,
                  paragraphs, and educational content.
                </p>
              </div>
            </div>
          </section>
        </div>
      )}

      {/* Start new document */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={onStartNew}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-violet-300 hover:bg-violet-50 hover:text-violet-700"
        >
          <RotateCcw size={17} />
          Start a new document
        </button>
      </div>
    </div>
  );
}