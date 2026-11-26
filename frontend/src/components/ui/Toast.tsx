import { useEffect } from "react";
import {
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  Info,
  X,
} from "lucide-react";

import type { ToastType } from "../../hooks/useToast";

interface ToastProps {
  message: string;
  type: ToastType;
  onClose: () => void;
  duration?: number;
}

const toastConfig = {
  success: {
    title: "Success",
    icon: CheckCircle2,
    styles: "border-emerald-200 bg-emerald-50 text-emerald-600",
  },
  error: {
    title: "Error",
    icon: AlertCircle,
    styles: "border-red-200 bg-red-50 text-red-600",
  },
  warning: {
    title: "Warning",
    icon: AlertTriangle,
    styles: "border-amber-200 bg-amber-50 text-amber-600",
  },
  info: {
    title: "Information",
    icon: Info,
    styles: "border-blue-200 bg-blue-50 text-blue-600",
  },
};

export default function Toast({
  message,
  type,
  onClose,
  duration = 3000,
}: ToastProps) {
  const config = toastConfig[type];
  const Icon = config.icon;

  useEffect(() => {
    if (duration <= 0) return;

    const timer = window.setTimeout(onClose, duration);

    return () => window.clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div
      role={type === "error" ? "alert" : "status"}
      className="fixed right-5 top-5 z-50 w-[calc(100%-2.5rem)] max-w-sm animate-in slide-in-from-top-3 fade-in"
    >
      <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-xl">
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${config.styles}`}
        >
          <Icon size={20} />
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-slate-900">
            {config.title}
          </p>

          <p className="mt-1 break-words text-sm text-slate-600">
            {message}
          </p>
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label="Close notification"
          className="rounded-lg p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
        >
          <X size={16} />
        </button>
      </div>
    </div>
  );
}