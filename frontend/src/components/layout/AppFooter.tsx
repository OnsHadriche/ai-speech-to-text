import { Cloud } from "lucide-react";

export default function AppFooter() {
  return (
    <footer className="mt-8 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-400">
      <Cloud size={14} />

      <span>
        Local audio processing · AI-powered document structuring
      </span>
    </footer>
  );
}