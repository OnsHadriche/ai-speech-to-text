import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
  size?: number;
  text?: string;
  className?: string;
}

export default function LoadingSpinner({
  size = 20,
  text,
  className = "",
}: LoadingSpinnerProps) {
  return (
    <div
      className={`inline-flex items-center gap-2 ${className}`}
      role="status"
      aria-live="polite"
    >
      <Loader2
        size={size}
        className="animate-spin text-violet-600"
        aria-hidden="true"
      />

      {text && (
        <span className="text-sm text-slate-500">
          {text}
        </span>
      )}

      {!text && (
        <span className="sr-only">Loading...</span>
      )}
    </div>
  );
}