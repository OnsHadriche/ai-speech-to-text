import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import {
  AudioLines,
  FileAudio,
  Upload,
  X,
  CheckCircle2,
  AlertCircle,
  Mic,
  StopCircle,
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
  onFileSelected?: (
    file: File,
    sourceType: "upload" | "microphone",
  ) => void;
}
type InputMode = "upload" | "record";

function formatFileSize(size: number): string {
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

function formatRecordingTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  return `${String(minutes).padStart(2, "0")}:${String(
    remainingSeconds,
  ).padStart(2, "0")}`;
}

function AudioInput({ onFileSelected }: AudioInputProps) {
  // Input mode
  const [inputMode, setInputMode] = useState<InputMode>("upload");

  // File and audio preview
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const audioUrlRef = useRef<string | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  // Microphone recording
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [recordingError, setRecordingError] = useState("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<number | null>(null);

  // Cleanup resources when component unmounts
  useEffect(() => {
    return () => {
      // Release preview URL
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }

      // Stop microphone tracks
      streamRef.current?.getTracks().forEach((track) => track.stop());

      // Stop recording timer
      if (recordingTimerRef.current !== null) {
        window.clearInterval(recordingTimerRef.current);
      }

      // Stop recorder if still active
      if (
        mediaRecorderRef.current &&
        mediaRecorderRef.current.state !== "inactive"
      ) {
        mediaRecorderRef.current.onstop = null;
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  // Validate file
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

  // Handle selected file or recorded audio
  function handleFile(file: File, sourceType: "upload"|"microphone"="upload") {
    if (!validateFile(file)) {
      return;
    }

    // Revoke previous preview URL
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
    }

    // Create preview URL
    const newAudioUrl = URL.createObjectURL(file);
    audioUrlRef.current = newAudioUrl;

    setAudioUrl(newAudioUrl);
    setSelectedFile(file);
    setRecordingError("");

    onFileSelected?.(file,sourceType);
  }

  // File input handler
  function handleFileInput(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (file) {
      handleFile(file);
    }

    // Allow selecting the same file again
    event.target.value = "";
  }

  // Drag and drop handler
  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];

    if (file) {
      handleFile(file);
    }
  }

  // Remove selected audio
  function removeFile() {
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }

    setSelectedFile(null);
    setAudioUrl(null);
    setError("");
    setRecordingError("");

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
    }
  }

  // Stop recording
  function stopRecording() {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }

    setIsRecording(false);

    if (recordingTimerRef.current !== null) {
      window.clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
  }

  // Start microphone recording
  async function startRecording() {
    try {
      setRecordingError("");
      setError("");

      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          "Microphone recording is not supported by this browser.",
        );
      }

      // Request microphone with speech-friendly settings
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 48000,
          sampleSize: 16,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;
      recordingChunksRef.current = [];

      // Choose supported recording format
      const mimeType = MediaRecorder.isTypeSupported(
        "audio/webm;codecs=opus",
      )
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : "";

      // Create recorder with speech-friendly bitrate
      const recorder = mimeType
        ? new MediaRecorder(stream, {
            mimeType,
            audioBitsPerSecond: 128000,
          })
        : new MediaRecorder(stream, {
            audioBitsPerSecond: 128000,
          });

      mediaRecorderRef.current = recorder;

      // Collect audio chunks
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordingChunksRef.current.push(event.data);
        }
      };

      // Create file when recording stops
      recorder.onstop = () => {
        const blob = new Blob(recordingChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });

        const extension = blob.type.includes("mp4") ? "m4a" : "webm";

        const recordedFile = new File(
          [blob],
          `recording-${Date.now()}.${extension}`,
          {
            type: blob.type,
          },
        );

        handleFile(recordedFile,"microphone");

        // Release microphone
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      };

      recorder.start();

      setIsRecording(true);
      setRecordingTime(0);

      recordingTimerRef.current = window.setInterval(() => {
        setRecordingTime((previous) => previous + 1);
      }, 1000);
    } catch (error) {
      // Release microphone if setup fails
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;

      console.error("Microphone error:", error);

      setRecordingError(
        error instanceof Error
          ? error.message
          : "Unable to access the microphone.",
      );
    }
  }

  return (
    <div className="space-y-5">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_EXTENSIONS.join(",")}
        onChange={handleFileInput}
        className="hidden"
      />

      {/* Input mode selector */}
      {!selectedFile && (
        <div className="grid grid-cols-2 gap-4">
          {/* Upload button */}
          <button
            type="button"
            onClick={() => setInputMode("upload")}
            disabled={isRecording}
            className={`flex items-center justify-center gap-3 rounded-2xl border p-5 transition-all ${
              inputMode === "upload"
                ? "border-violet-500 bg-violet-50 text-violet-700 shadow-sm ring-2 ring-violet-100"
                : "border-slate-200 bg-white text-slate-600 hover:border-violet-300 hover:bg-violet-50/50"
            } disabled:cursor-not-allowed disabled:opacity-50`}
          >
            <Upload size={20} />

            <div className="text-left">
              <p className="font-semibold">Upload audio</p>
              <p className="text-xs opacity-70">Select an existing file</p>
            </div>
          </button>

          {/* Record button */}
          <button
            type="button"
            onClick={() => setInputMode("record")}
            disabled={isRecording}
            className={`flex items-center justify-center gap-3 rounded-2xl border p-5 transition-all ${
              inputMode === "record"
                ? "border-violet-500 bg-violet-50 text-violet-700 shadow-sm ring-2 ring-violet-100"
                : "border-slate-200 bg-white text-slate-600 hover:border-violet-300 hover:bg-violet-50/50"
            } disabled:cursor-not-allowed disabled:opacity-50`}
          >
            <Mic size={20} />

            <div className="text-left">
              <p className="font-semibold">Record audio</p>
              <p className="text-xs opacity-70">Use your microphone</p>
            </div>
          </button>
        </div>
      )}

      {/* Upload mode */}
      {!selectedFile && inputMode === "upload" && (
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
              Drag and drop your audio file here, or browse your computer.
            </p>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="mt-6 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-blue-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-200 transition hover:-translate-y-0.5 hover:shadow-xl"
            >
              <Upload size={17} />
              Browse files
            </button>

            {/* Supported formats */}
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

      {/* Recording mode */}
      {!selectedFile && inputMode === "record" && (
        <div className="rounded-2xl border border-violet-200 bg-gradient-to-br from-violet-50/70 to-blue-50/70 p-8 md:p-12">
          <div className="mx-auto flex max-w-xl flex-col items-center text-center">
            <div
              className={`mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-sm ${
                isRecording ? "text-red-500" : "text-violet-600"
              }`}
            >
              <Mic size={28} />
            </div>

            <h3 className="text-xl font-semibold text-slate-900">
              {isRecording ? "Recording in progress" : "Record your audio"}
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              {isRecording
                ? "Speak clearly. Stop recording when you are finished."
                : "Record directly from your microphone."}
            </p>

            {/* Recording timer */}
            {isRecording && (
              <div className="mt-6 flex items-center gap-3 rounded-full border border-red-100 bg-white px-5 py-3">
                <span className="h-3 w-3 animate-pulse rounded-full bg-red-500" />

                <span className="font-mono text-lg font-semibold text-red-600">
                  {formatRecordingTime(recordingTime)}
                </span>
              </div>
            )}

            {/* Start / Stop */}
            {!isRecording ? (
              <button
                type="button"
                onClick={startRecording}
                className="mt-6 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-blue-500 px-6 py-3 font-semibold text-white shadow-lg shadow-violet-200 transition hover:-translate-y-0.5 hover:shadow-xl"
              >
                <Mic size={18} />
                Start recording
              </button>
            ) : (
              <button
                type="button"
                onClick={stopRecording}
                className="mt-6 inline-flex items-center gap-2 rounded-xl bg-red-500 px-6 py-3 font-semibold text-white shadow-lg shadow-red-200 transition hover:bg-red-600"
              >
                <StopCircle size={18} />
                Stop recording
              </button>
            )}

            {/* Recording error */}
            {recordingError && (
              <div className="mt-5 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                <AlertCircle size={18} className="mt-0.5 shrink-0" />
                <p>{recordingError}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Selected audio */}
      {selectedFile && audioUrl && (
        <div className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
          {/* File details */}
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

            {/* Remove audio */}
            <button
              type="button"
              onClick={removeFile}
              className="rounded-lg p-2 text-slate-400 transition hover:bg-red-50 hover:text-red-500"
              aria-label="Remove audio file"
            >
              <X size={18} />
            </button>
          </div>

          {/* Native audio player */}
          <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-700">
              <AudioLines size={18} className="text-violet-600" />
              Audio preview
            </div>

            <audio
              ref={audioRef}
              src={audioUrl}
              controls
              preload="metadata"
              className="w-full"
            />
          </div>

          {/* Change audio */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="mt-4 text-sm font-medium text-violet-600 transition hover:text-violet-800"
          >
            Choose another file
          </button>
        </div>
      )}

      {/* File validation error */}
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