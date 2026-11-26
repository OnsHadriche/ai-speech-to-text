import { AlertCircle } from "lucide-react";

interface TranscriptionErrorProps {
  message: string;
}

export default function TranscriptionError({
  message,
}: TranscriptionErrorProps) {
  if (!message) return null;

  return (
    <div className="mt-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      <AlertCircle size={18} className="mt-0.5 shrink-0" />

      <div>
        <p className="font-semibold">Transcription failed</p>
        <p className="mt-1">{message}</p>
      </div>
    </div>
  );
}