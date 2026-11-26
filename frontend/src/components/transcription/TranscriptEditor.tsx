
import { Copy, FileText } from "lucide-react";

interface TranscriptEditorProps {
  transcript: string;
  onTranscriptChange: (value: string) => void;
  wordCount: number;
}

export default function TranscriptEditor({
  transcript,
  onTranscriptChange,
  wordCount,
}: TranscriptEditorProps) {
  const characterCount = transcript.length;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(transcript);
    } catch (error) {
      console.error("Failed to copy transcript:", error);
    }
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      {/* Header */}
      <div className="flex flex-col gap-3 border-b border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <FileText size={18} className="text-violet-600" />

          <div>
            <h3 className="font-semibold text-slate-900">
              Transcript
            </h3>
            <p className="text-xs text-slate-500">
              Review and edit the generated text
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          disabled={!transcript}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Copy size={15} />
          Copy transcript
        </button>
      </div>

      {/* Editor */}
      <div className="p-4">
        <textarea
          value={transcript}
          onChange={(event) => onTranscriptChange(event.target.value)}
          placeholder="Your transcript will appear here..."
          rows={12}
          className="min-h-[300px] w-full resize-y rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-7 text-slate-800 outline-none transition focus:border-violet-400 focus:bg-white focus:ring-2 focus:ring-violet-100"
          aria-label="Editable transcript"
        />
      </div>

      {/* Footer */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 bg-slate-50 px-4 py-3">
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span>
            <strong className="text-slate-700">{wordCount}</strong> words
          </span>

          <span>
            <strong className="text-slate-700">
              {characterCount}
            </strong>{" "}
            characters
          </span>
        </div>

        <span className="text-xs text-emerald-600">
          ✓ Editable transcript
        </span>
      </div>
    </section>
  );
}
