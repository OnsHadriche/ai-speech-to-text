import type { ReactNode } from "react";

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-[#F8F9FF] text-slate-900">
      {children}
    </div>
  );
}