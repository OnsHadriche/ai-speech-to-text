
import { useEffect } from "react";
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Info,
  X,
} from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info";

interface ToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose: () => void;
}

const toastStyles: Record<
  ToastType,
  {
    icon: typeof CheckCircle2;
    iconColor: string;
    iconBackground: string;
    border: string;
    title: string;
  }
> = {
  success: {
    icon: CheckCircle2,
    iconColor: "text-emerald-600",
    iconBackground: "bg-emerald-50",
    border: "border-emerald-200",
    title: "Success",
  },
  error: {
    icon: AlertCircle,
    iconColor: "text-red-600",
    iconBackground: "bg-red-50",
    border: "border-red-200",
    title: "Error",
  },
  warning: {
    icon: AlertTriangle,
    iconColor: "text-amber-600",
    iconBackground: "bg-amber-50",
    border: "border-amber-200",
    title: "Warning",
  },
  info: {
    icon: Info,
    iconColor: "text-blue-600",
    iconBackground: "bg-blue-50",
    border: "border-blue-200",
    title: "Information",
  },
};

export default function Toast({
  message,
  type = "success",
  duration = 3000,
  onClose,
}: ToastProps) {
  const style = toastStyles[type];
  const Icon = style.icon;

  useEffect(() => {
    if (duration <= 0) return;

    const timer = window.setTimeout(onClose, duration);

    return () => window.clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div
      role={type === "error" ? "alert" : "status"}
      aria-live="polite"
      className="fixed right-5 top-5 z-[100] w-[calc(100%-2.5rem)] max-w-sm animate-in slide-in-from-top-3 fade-in duration-300"
    >
      <div
        className={`flex items-start gap-3 rounded-xl border ${style.border} bg-white p-4 shadow-xl shadow-slate-200/60`}
      >
        {/* Icon */}
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${style.iconBackground} ${style.iconColor}`}
        >
          <Icon size={20} />
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1 pt-0.5">
          <p className="text-sm font-semibold text-slate-900">
            {style.title}
          </p>

          <p className="mt-1 break-words text-sm leading-5 text-slate-600">
            {message}
          </p>
        </div>

        {/* Close button */}
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
