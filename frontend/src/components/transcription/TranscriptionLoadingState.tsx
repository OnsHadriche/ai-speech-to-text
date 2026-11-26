import LoadingSpinner from "../ui/LoadingSpinner";

export default function TranscriptionLoadingState() {
  return (
    <div className="mt-5 rounded-xl border border-violet-100 bg-white/70 p-5">
      <div className="flex flex-col items-center gap-4 text-center">
        <LoadingSpinner
          size={32}
          text="Transcribing your audio..."
          className="flex-col"
        />

        <div>
          <p className="font-medium text-violet-900">
            Transcription in progress
          </p>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            Processing your audio. This may take a few moments
            depending on its duration.
          </p>
        </div>
      </div>
    </div>
  );
}