import { AudioLines } from "lucide-react";
import StatusBadge from "../ui/StatusBadge";

interface AppHeaderProps {
  isBackendOnline: boolean | null;
}

export default function AppHeader({
  isBackendOnline,
}: AppHeaderProps) {
  const status = 
    isBackendOnline === null
      ? "checking"
      : isBackendOnline
        ? "online"
        : "offline";

  return (
    <header className="border-b border-slate-200/70 bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 md:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-blue-500 text-white shadow-md shadow-violet-200">
            <AudioLines size={21} />
          </div>

          <div>
            <h1 className="text-lg font-bold tracking-tight text-slate-900">
              Speech To Docx Studio AI
            </h1>

            <p className="text-xs text-slate-500">
              AI-powered transcription and document generation
            </p>
          </div>
        </div>

        <StatusBadge status={status} />
      </div>
    </header>
  );
}