interface StatusBadgeProps {
  status: "online" | "offline" | "checking";
}

const statusConfig = {
  online: {
    label: "Backend connected",
    styles: "border-emerald-200 bg-emerald-50 text-emerald-700",
    dot: "bg-emerald-500",
  },
  offline: {
    label: "Backend offline",
    styles: "border-red-200 bg-red-50 text-red-700",
    dot: "bg-red-500",
  },
  checking: {
    label: "Checking backend...",
    styles: "border-slate-200 bg-slate-50 text-slate-500",
    dot: "bg-slate-400 animate-pulse",
  },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <div
      className={`flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-medium ${config.styles}`}
    >
      <span className={`h-2 w-2 rounded-full ${config.dot}`} />
      {config.label}
    </div>
  );
}