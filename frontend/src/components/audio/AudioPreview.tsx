import { AudioLines } from "lucide-react";
import { useRef, useState } from "react";

interface AudioPreviewProps {
  src: string;
}

export function AudioPreview({ src }: AudioPreviewProps) {
  const audioRef = useRef<HTMLAudioElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const waveform = [
    12, 18, 10, 22, 16, 28, 14, 24, 32, 20, 38, 26, 18, 30, 42, 24,
    36, 48, 28, 40, 22, 34, 46, 30, 18, 36, 26, 42, 32, 20, 44, 28,
    38, 24, 50, 34, 22, 40, 28, 46, 32, 18, 36, 24, 42, 30, 20, 38,
    26, 44, 34, 22, 40, 28, 48, 32, 18, 36, 24, 42, 30, 20, 38, 26,
    44, 34, 22, 40, 28, 46, 32, 18, 36, 24, 42, 30, 20, 38, 26,
  ];
  const [playbackError, setPlaybackError] = useState("");
  const progress =
    duration > 0 ? (currentTime / duration) * 100 : 0;

  function formatTime(seconds: number): string {
    if (!Number.isFinite(seconds)) return "0:00";

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);

    return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
  }
    async function togglePlayback() {
    const audio = audioRef.current;

    if (!audio) {
        setPlaybackError("Audio player is not initialized.");
        return;
    }

    setPlaybackError("");

    try {
        if (audio.paused) {
        await audio.play();
        } else {
        audio.pause();
        }
    } catch (error) {
        console.error("Playback failed:", error);

        setPlaybackError(
        "Unable to play this audio file. The audio format may not be supported by your browser.",
        );

        setIsPlaying(false);
    }
}

  function handleSeek(value: number) {
    const audio = audioRef.current;

    if (!audio || !duration) return;

    const newTime = (value / 100) * duration;

    audio.currentTime = newTime;
    setCurrentTime(newTime);
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-violet-100 bg-gradient-to-br from-white via-violet-50/70 to-blue-50/80 p-5 shadow-sm">
      {/* Background decoration */}
      <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-violet-200/30 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-16 -left-16 h-40 w-40 rounded-full bg-blue-200/30 blur-3xl" />

      {/* Hidden native audio element */}
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onLoadedMetadata={(event) => {
          setDuration(event.currentTarget.duration || 0);
          setCurrentTime(0);
          setPlaybackError("")
        }}
        onTimeUpdate={(event) => {
          setCurrentTime(event.currentTarget.currentTime);
        }}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => {setIsPlaying(false); setCurrentTime(0)}}
        onError={(event)=>{
            console.log("Audio loading error",event.currentTarget.error)
            setPlaybackError("This audio file could not be loaded or is not supported by your browser.")
            setIsPlaying(false)
        }}
      />

      <div className="relative z-10">
        {/* Header */}
        <div className="mb-5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-100 text-violet-600">
              <AudioLines size={16} />
            </div>

            <span className="text-sm font-semibold text-slate-700">
              Audio preview
            </span>
          </div>

          <span className="flex items-center gap-1.5 rounded-full border border-violet-100 bg-white/80 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-violet-600">
            <span className="h-1.5 w-1.5 rounded-full bg-violet-500" />
            Original audio
          </span>
        </div>

        {/* Main player */}
        <div className="flex items-center gap-4">
          {/* Artwork */}
          <div className="relative flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-br from-violet-500 via-purple-500 to-blue-500 shadow-lg shadow-violet-200">
            <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent" />

            <div className="relative flex h-12 items-center justify-center gap-1">
              {[16, 24, 34, 20, 42, 28, 36, 18, 30].map(
                (height, index) => (
                  <div
                    key={index}
                    className={`w-1 rounded-full bg-white/90 ${
                      isPlaying ? "animate-pulse" : ""
                    }`}
                    style={{
                      height: `${height}px`,
                      animationDelay: `${index * 80}ms`,
                    }}
                  />
                ),
              )}
            </div>

            <div className="absolute bottom-2 right-2 rounded-full bg-white/20 p-1 backdrop-blur-sm">
              <AudioLines size={12} className="text-white" />
            </div>
          </div>

          {/* File info */}
          <div className="min-w-0 flex-1">
            <div className="mb-1 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-violet-500">
              <AudioLines size={12} />
              {isPlaying ? "Now playing" : "Ready to play"}
            </div>

            <h4 className="truncate text-base font-semibold text-slate-900">
              Your audio recording
            </h4>

            <p className="mt-1 text-xs text-slate-500">
              Listen before transcription
            </p>

            <div className="mt-2 flex items-center gap-2 text-xs text-slate-400">
              <span>{formatTime(currentTime)}</span>
              <span>•</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Play button */}
          <button
            type="button"
            onClick={togglePlayback}
            aria-label={isPlaying ? "Pause audio" : "Play audio"}
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-blue-500 text-white shadow-lg shadow-violet-200 transition hover:scale-105 hover:shadow-xl active:scale-95"
          >
            {isPlaying ? (
              <span className="flex gap-1">
                <span className="h-4 w-1.5 rounded-sm bg-white" />
                <span className="h-4 w-1.5 rounded-sm bg-white" />
              </span>
            ) : (
              <svg
                viewBox="0 0 24 24"
                fill="currentColor"
                className="ml-0.5 h-5 w-5"
              >
                <path d="M8 5.5v13l10-6.5z" />
              </svg>
            )}
          </button>
        </div>

        {/* Waveform */}
        <div className="mt-5 flex h-12 items-center gap-[3px] overflow-hidden">
          {waveform.map((height, index) => {
            const isActive =
              (index / waveform.length) * 100 <= progress;

            return (
              <div
                key={index}
                className={`flex-1 rounded-full transition-colors duration-200 ${
                  isActive
                    ? "bg-gradient-to-t from-violet-600 to-blue-500"
                    : "bg-violet-200/70"
                }`}
                style={{
                  height: `${height}%`,
                  minWidth: "2px",
                }}
              />
            );
          })}
        </div>

        {/* Seek bar */}
        <input
          type="range"
          min={0}
          max={100}
          step={0.1}
          value={progress}
          onChange={(event) => handleSeek(Number(event.target.value))}
          aria-label="Audio progress"
          className="mt-2 h-1.5 w-full cursor-pointer appearance-none rounded-full bg-violet-100 accent-violet-600"
          style={{
            background: `linear-gradient(to right, #7c3aed ${progress}%, #e9d5ff ${progress}%)`,
          }}
        />

        {/* Footer */}
        <div className="mt-3 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Preview your audio
          </span>

          <span className="text-xs font-medium text-violet-600">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
      </div>
    </div>
  );
}
