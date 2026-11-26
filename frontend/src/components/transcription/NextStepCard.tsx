
import { ArrowRight, Sparkles } from "lucide-react";
import Button from "../ui/Button";

interface NextStepCardProps {
  onContinue: () => void;
}

export default function NextStepCard({
  onContinue,
}: NextStepCardProps) {
  return (
    <section className="rounded-2xl border border-violet-200 bg-violet-50/60 p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-violet-600 shadow-sm">
          <Sparkles size={20} />
        </div>

        <div className="flex-1">
          <h3 className="font-semibold text-slate-900">
            Ready for the next step?
          </h3>

          <p className="mt-1 text-sm leading-6 text-slate-600">
            Your transcript is ready. Continue to analyze and organize
            the text into a structured document.
          </p>
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button
          onClick={onContinue}
          icon={<ArrowRight size={16} />}
        >
          Continue to structuring
        </Button>
      </div>
    </section>
  );
}
