import {useEffect, useRef, useState } from "react";
import {
  AudioLines,
  FileAudio,
  Upload,
  X,
  Play,
  Pause,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB

const ALLOWED_EXTENSIONS = [
  ".wav",
  ".mp3",
  ".m4a",
  ".mp4",
  ".webm",
  ".ogg",
  ".flac",
];

interface AudioInputProps {
  onFileSelected?: (file: File) => void;
}

function formatFileSize(size: number): string {
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

function AudioInput({ onFileSelected }: AudioInputProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioUrlRef = useRef<string | null>(null);
  useEffect(() => {
  return () => {
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
    }
  };
}, []);
  function validateFile(file: File): boolean {
    const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError(
        "Unsupported file format. Please select a supported audio file.",
      );

      return false;
    }

    if (file.size === 0) {
      setError("The selected file is empty.");

      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("File size exceeds the maximum allowed size of 100 MB.");

      return false;
    }

    setError("");

    return true;
  }

  function handleFile(file: File) {
    if (!validateFile(file)) {
      return;
    }
    // Revoke the previous audio URL if it exists
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
    }
    // Create a new audio URL for the selected file
    const newAudioUrl = URL.createObjectURL(file);
    audioUrlRef.current = newAudioUrl;
    
    setAudioUrl(newAudioUrl);
    setSelectedFile(file);
    setIsPlaying(false);

    onFileSelected?.(file);
  }

  function handleFileInput(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];

    if (file) {
      handleFile(file);
    }

    // Allows selecting the same file again.
    event.target.value = "";
  }

  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();

    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];

    if (file) {
      handleFile(file);
    }
  }

  function removeFile() {
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
    setSelectedFile(null);
    setAudioUrl(null);
    setError("");
    setIsPlaying(false);

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";

    }
  }

  async function togglePlayback() {
    if (!audioRef.current) {
      return;
    }

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      try {
        await audioRef.current.play();
        setIsPlaying(true);
      } catch {
        setError("Unable to play this audio file.");
      }
    }
  }

  return (
    <div className="space-y-5">
      {/* File input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_EXTENSIONS.join(",")}
        onChange={handleFileInput}
        className="hidden"
      />

      {/* Dropzone */}
      {!selectedFile && (
        <div
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`rounded-2xl border-2 border-dashed p-8 transition-all md:p-12 ${
            isDragging
              ? "border-violet-500 bg-violet-100/70"
              : "border-violet-200 bg-gradient-to-br from-violet-50/70 to-blue-50/70"
          }`}
        >
          <div className="mx-auto max-w-xl text-center">
            <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-violet-600 shadow-sm">
              <Upload size={28} />
            </div>

            <h3 className="text-xl font-semibold text-slate-900">
              Upload your audio
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Drag and drop your audio file here, or browse your
              computer.
            </p>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="mt-6 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-blue-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-200 transition hover:-translate-y-0.5 hover:shadow-xl"
            >
              <Upload size={17} />
              Browse files
            </button>

            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {ALLOWED_EXTENSIONS.map((extension) => (
                <span
                  key={extension}
                  className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-500"
                >
                  {extension}
                </span>
              ))}
            </div>

            <p className="mt-4 text-xs text-slate-400">
              Maximum file size: 100 MB
            </p>
          </div>
        </div>
      )}

      {/* Selected audio */}
      {selectedFile && audioUrl && (
        <div className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div className="flex min-w-0 items-center gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
                <FileAudio size={23} />
              </div>

              <div className="min-w-0">
                <h4 className="truncate font-semibold text-slate-900">
                  {selectedFile.name}
                </h4>

                <p className="mt-1 text-sm text-slate-500">
                  {formatFileSize(selectedFile.size)}
                </p>

                <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-600">
                  <CheckCircle2 size={14} />
                  File validated successfully
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={removeFile}
              className="rounded-lg p-2 text-slate-400 transition hover:bg-red-50 hover:text-red-500"
              aria-label="Remove audio file"
            >
              <X size={18} />
            </button>
          </div>

          {/* Audio player */}
          <div className="mt-5 flex items-center gap-3 rounded-xl bg-slate-50 p-3">
            <button
              type="button"
              onClick={togglePlayback}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-r from-violet-600 to-blue-500 text-white shadow-md"
            >
              {isPlaying ? <Pause size={17} /> : <Play size={17} />}
            </button>

            <div className="flex flex-1 items-center gap-1">
              {Array.from({ length: 30 }).map((_, index) => (
                <div
                  key={index}
                  className="flex-1 rounded-full bg-gradient-to-t from-violet-400 to-blue-400"
                  style={{
                    height: `${12 + ((index * 17) % 28)}px`,
                    opacity: isPlaying ? 1 : 0.6,
                  }}
                />
              ))}
            </div>

            <AudioLines
              size={18}
              className="shrink-0 text-violet-500"
            />
          </div>

          <audio
            ref={audioRef}
            src={audioUrl}
            onEnded={() => setIsPlaying(false)}
            onPause={() => setIsPlaying(false)}
            onPlay={() => setIsPlaying(true)}
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="mt-4 text-sm font-medium text-violet-600 transition hover:text-violet-800"
          >
            Choose another file
          </button>
        </div>
      )}

      {/* Validation error */}
      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />

          <p>{error}</p>
        </div>
      )}
    </div>
  );
}

export default AudioInput;