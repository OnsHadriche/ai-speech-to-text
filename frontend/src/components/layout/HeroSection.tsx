import { Sparkles } from "lucide-react";

export default function HeroSection() {
  return (
    <section className="mb-8">
      <div className="inline-flex items-center gap-2 rounded-full border border-violet-100 bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-700">
        <Sparkles size={14} />
        AI-powered learning document creation
      </div>

      <h2 className="mt-4 max-w-3xl text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
        Transform your audio into{" "}
        <span className="bg-gradient-to-r from-violet-600 to-blue-500 bg-clip-text text-transparent">
          structured learning documents.
        </span>
      </h2>

      <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">
        Transcribe your lessons, organize educational content with AI,
        review the structure, and generate editable Word documents.
      </p>
    </section>
  );
}