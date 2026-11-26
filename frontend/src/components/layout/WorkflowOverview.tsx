import {
  AudioLines,
  FileText,
  Sparkles,
} from "lucide-react";

import Card from "../ui/Card";

const workflowSteps = [
  {
    number: "01",
    title: "Transcribe",
    description:
      "Convert your audio into text using speech recognition.",
    icon: AudioLines,
    iconStyles: "bg-violet-50 text-violet-600",
  },
  {
    number: "02",
    title: "Structure with AI",
    description:
      "Identify definitions, headings, examples, paragraphs, and educational content.",
    icon: Sparkles,
    iconStyles: "bg-blue-50 text-blue-600",
  },
  {
    number: "03",
    title: "Review & Export",
    description:
      "Confirm the structure and generate your editable Word document.",
    icon: FileText,
    iconStyles: "bg-emerald-50 text-emerald-600",
  },
];

function WorkflowStepCard({
  step,
}: {
  step: (typeof workflowSteps)[number];
}) {
  const Icon = step.icon;

  return (
    <Card className="p-5">
      <div
        className={`mb-4 flex h-9 w-9 items-center justify-center rounded-xl ${step.iconStyles}`}
      >
        <Icon size={18} />
      </div>

      <p className="text-sm font-semibold text-slate-900">
        {step.number} · {step.title}
      </p>

      <p className="mt-2 text-xs leading-5 text-slate-500">
        {step.description}
      </p>
    </Card>
  );
}

export default function WorkflowOverview() {
  return (
    <section className="mt-6 grid gap-4 md:grid-cols-3">
      {workflowSteps.map((step) => (
        <WorkflowStepCard key={step.number} step={step} />
      ))}
    </section>
  );
}