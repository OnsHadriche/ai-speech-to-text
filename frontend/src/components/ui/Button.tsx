import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";

type ButtonVariant = "primary" | "secondary" | "outline";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  loading?: boolean;
  loadingText?: string;
  icon?: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-violet-600 to-blue-500 text-white shadow-lg shadow-violet-200 hover:-translate-y-0.5 hover:shadow-xl",
  secondary:
    "bg-slate-100 text-slate-700 hover:bg-slate-200",
  outline:
    "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
};

export default function Button({
  children,
  variant = "primary",
  loading = false,
  loadingText,
  icon,
  disabled,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={`
        inline-flex items-center justify-center gap-2
        rounded-xl px-6 py-3 text-sm font-semibold
        transition-all duration-200
        disabled:cursor-not-allowed disabled:opacity-50
        ${variantStyles[variant]}
        ${className}
      `}
      {...props}
    >
      {loading ? (
        <>
          <Loader2 size={17} className="animate-spin" />
          {loadingText ?? "Loading..."}
        </>
      ) : (
        <>
          {icon}
          {children}
        </>
      )}
    </button>
  );
}