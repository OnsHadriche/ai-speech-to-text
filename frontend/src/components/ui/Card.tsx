import type { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export default function Card({
  children,
  className = "",
  ...props
}: CardProps) {
  return (
    <div
      className={`
        rounded-2xl border border-slate-200
        bg-white shadow-sm
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
}