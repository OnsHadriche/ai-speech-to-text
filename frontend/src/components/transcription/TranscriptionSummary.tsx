import { CheckCircle2, Languages } from "lucide-react";

interface TranscriptionSummaryProps {
  language: string | null;
  duration: number | null;
  wordCount: number;
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "--:--";

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
}

export default function TranscriptionSummary({
    language,
    duration,
    wordCount,
}: TranscriptionSummaryProps) {
  return (
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
            Your audio has been converted to text. Review and correct
            the transcript before continuing.
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {language && (
          <div className="flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-sm text-slate-600">
            <Languages size={15} className="text-violet-500" />
            Language: <strong>{language}</strong>
          </div>
        )}

        {duration !== null && (
          <div className="rounded-lg bg-white px-3 py-2 text-sm text-slate-600">
            Duration:{" "}
            <strong>{formatDuration(duration)}</strong>
          </div>
        )}

        <div className="rounded-lg bg-white px-3 py-2 text-sm text-slate-600">
          Words: <strong>{wordCount}</strong>
        </div>
      </div>
    </section>
  );
}