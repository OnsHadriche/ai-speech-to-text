import { useEffect, useState } from "react";
import {
  AudioLines,
  CheckCircle2,
  Cloud,
  FileAudio,
  Sparkles,
  AlertCircle,
  Loader2,
  RotateCcw,
} from "lucide-react";

import AudioInput from "./components/audio/AudioInput";
import { uploadAudio } from "./services/jobs";
import type { JobResponse, AudioSourceType } from "./services/jobs";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function App() {
  // Backend status
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "connected" | "disconnected"
  >("checking");

  // Audio selection
  const [selectedAudio, setSelectedAudio] = useState<File | null>(null);
  const [sourceType, setSourceType] = useState<AudioSourceType>("upload");

  // Upload state
  const [uploadedJob, setUploadedJob] = useState<JobResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  // Reset AudioInput component
  const [audioInputKey, setAudioInputKey] = useState(0);

  // Check backend health
  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await fetch(`${API_URL}/api/health`);

        if (!response.ok) {
          throw new Error("Backend request failed");
        }

        await response.json();
        setBackendStatus("connected");
      } catch {
        setBackendStatus("disconnected");
      }
    }

    checkBackend();
  }, []);

  // Handle selected or recorded audio
  function handleAudioSelected(
    file: File,
    selectedSourceType: AudioSourceType,
  ) {
    setSelectedAudio(file);
    setSourceType(selectedSourceType);
    setUploadedJob(null);
    setUploadError("");
  }

  // Upload audio to backend
  async function handleUploadAudio() {
    if (!selectedAudio) {
      setUploadError("Please select or record an audio file first.");
      return;
    }

    if (backendStatus !== "connected") {
      setUploadError(
        "The backend is not available. Please start the backend and try again.",
      );
      return;
    }

    try {
      setIsUploading(true);
      setUploadError("");
      setUploadedJob(null);

      const job = await uploadAudio(selectedAudio, sourceType);

      setUploadedJob(job);
      console.log("Audio uploaded successfully:", job);
    } catch (error) {
      console.error("Upload error:", error);

      setUploadError(
        error instanceof Error
          ? error.message
          : "An unexpected error occurred during upload.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  // Start a new document workflow
  function handleStartNewDocument() {
    setSelectedAudio(null);
    setSourceType("upload");
    setUploadedJob(null);
    setUploadError("");
    setAudioInputKey((previous) => previous + 1);
  }

  return (
    <main className="app-background min-h-screen">
      {/* Header */}
      <header className="border-b border-white/70 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-blue-500 text-white shadow-lg shadow-violet-200">
              <AudioLines size={22} />
            </div>

            <div>
              <h1 className="text-lg font-bold tracking-tight">
                Speech To Docx <span className="gradient-text">Studio AI</span>
              </h1>

              <p className="text-xs text-slate-500">
                Audio to educational documents
              </p>
            </div>
          </div>

          {/* Backend status */}
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2">
            <span
              className={`h-2 w-2 rounded-full ${
                backendStatus === "connected"
                  ? "bg-emerald-500"
                  : backendStatus === "disconnected"
                    ? "bg-red-500"
                    : "animate-pulse bg-amber-400"
              }`}
            />

            <span className="text-xs font-medium text-slate-600">
              {backendStatus === "connected"
                ? "System ready"
                : backendStatus === "disconnected"
                  ? "Backend offline"
                  : "Connecting..."}
            </span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="mx-auto max-w-7xl px-6 py-12">
        {/* Hero */}
        <section className="mb-10">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-100 bg-violet-50 px-3 py-1.5 text-sm font-medium text-violet-700">
            <Sparkles size={15} />
            AI-powered document creation
          </div>

          <h2 className="max-w-3xl text-4xl font-bold leading-tight tracking-tight text-slate-900 md:text-5xl">
            Turn your audio into
            <br />
            <span className="gradient-text">
              structured learning documents.
            </span>
          </h2>

          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-500">
            Transcribe your lessons, organize educational content with AI, review
            the structure, and generate editable Word documents.
          </p>
        </section>

        {/* Workspace */}
        <section className="surface soft-shadow overflow-hidden">
          {/* Workspace header */}
          <div className="border-b border-slate-100 px-6 py-5 md:px-8">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
                <FileAudio size={20} />
              </div>

              <div>
                <h3 className="font-semibold text-slate-900">
                  Create a new document
                </h3>

                <p className="mt-1 text-sm text-slate-500">
                  Start with an audio recording or an existing audio file.
                </p>
              </div>
            </div>
          </div>

          {/* Workspace content */}
          <div className="p-6 md:p-8">
            {/* Audio input */}
            {!uploadedJob && (
              <>
                <AudioInput
                  key={audioInputKey}
                  onFileSelected={handleAudioSelected}
                />

                {/* Upload button */}
                {selectedAudio && (
                  <div className="mt-6 flex justify-end">
                    <button
                      type="button"
                      onClick={handleUploadAudio}
                      disabled={isUploading || backendStatus !== "connected"}
                      className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-blue-500 px-6 py-3 font-semibold text-white shadow-lg shadow-violet-200 transition hover:-translate-y-0.5 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
                    >
                      {isUploading ? (
                        <>
                          <Loader2 size={18} className="animate-spin" />
                          Uploading audio...
                        </>
                      ) : (
                        <>
                          <Cloud size={18} />
                          Upload & Continue
                        </>
                      )}
                    </button>
                  </div>
                )}

                {/* Upload error */}
                {uploadError && (
                  <div className="mt-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    <AlertCircle size={18} className="mt-0.5 shrink-0" />
                    <p>{uploadError}</p>
                  </div>
                )}

                {/* Backend offline warning */}
                {backendStatus === "disconnected" && (
                  <div className="mt-4 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                    <AlertCircle size={18} className="mt-0.5 shrink-0" />

                    <div>
                      <p className="font-semibold">Backend unavailable</p>
                      <p className="mt-1">
                        Start your FastAPI backend to upload and process audio.
                      </p>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Successful upload */}
            {uploadedJob && (
              <div className="space-y-6">
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6">
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white text-emerald-600">
                      <CheckCircle2 size={25} />
                    </div>

                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-emerald-900">
                        Audio uploaded successfully!
                      </h3>

                      <p className="mt-1 text-sm text-emerald-700">
                        Your audio has been stored and is ready for the next
                        processing step.
                      </p>
                    </div>
                  </div>

                  {/* Job details */}
                  <div className="mt-6 grid gap-4 sm:grid-cols-2">
                    <div className="rounded-xl border border-emerald-100 bg-white p-4">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                        Job ID
                      </p>

                      <p className="mt-2 break-all font-mono text-sm text-slate-700">
                        {uploadedJob.id}
                      </p>
                    </div>

                    <div className="rounded-xl border border-emerald-100 bg-white p-4">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                        File name
                      </p>

                      <p className="mt-2 break-all text-sm font-medium text-slate-700">
                        {uploadedJob.original_name}
                      </p>
                    </div>

                    <div className="rounded-xl border border-emerald-100 bg-white p-4">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                        Source
                      </p>

                      <p className="mt-2 text-sm font-medium capitalize text-slate-700">
                        {uploadedJob.source_type}
                      </p>
                    </div>

                    <div className="rounded-xl border border-emerald-100 bg-white p-4">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                        Status
                      </p>

                      <p className="mt-2 text-sm font-medium capitalize text-slate-700">
                        {uploadedJob.status.replace(/_/g, " ")}
                      </p>
                    </div>

                    {uploadedJob.duration_seconds !== null && (
                      <div className="rounded-xl border border-emerald-100 bg-white p-4">
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                          Duration
                        </p>

                        <p className="mt-2 text-sm font-medium text-slate-700">
                          {uploadedJob.duration_seconds.toFixed(2)} seconds
                        </p>
                      </div>
                    )}

                    <div className="rounded-xl border border-emerald-100 bg-white p-4">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                        File size
                      </p>

                      <p className="mt-2 text-sm font-medium text-slate-700">
                        {(uploadedJob.size_byte / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                </div>

                {/* Next step placeholder */}
                <div className="rounded-2xl border border-violet-200 bg-gradient-to-br from-violet-50/70 to-blue-50/70 p-6">
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-violet-600 shadow-sm">
                      <Sparkles size={20} />
                    </div>

                    <div>
                      <h3 className="font-semibold text-slate-900">
                        Ready for transcription
                      </h3>

                      <p className="mt-1 text-sm leading-6 text-slate-500">
                        The audio upload is complete. The next step will
                        transcribe the audio using the local speech recognition
                        system.
                      </p>
                    </div>
                  </div>
                </div>

                {/* New document button */}
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleStartNewDocument}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-violet-300 hover:bg-violet-50 hover:text-violet-700"
                  >
                    <RotateCcw size={17} />
                    Start a new document
                  </button>
                </div>
              </div>
            )}

            {/* Initial workspace placeholder */}
            {!selectedAudio && !uploadedJob && (
              <div className="mt-6 rounded-2xl border-2 border-dashed border-violet-200 bg-gradient-to-br from-violet-50/70 to-blue-50/70 p-8 md:p-12">
                <div className="mx-auto max-w-xl text-center">
                  <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-violet-600 shadow-sm">
                    <Cloud size={28} />
                  </div>

                  <h4 className="text-xl font-semibold text-slate-900">
                    Your audio workspace
                  </h4>

                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    Upload an audio file or record directly from your microphone.
                    Your transcript will then be analyzed and organized into
                    educational segments.
                  </p>

                  <div className="mt-6 flex flex-wrap justify-center gap-3">
                    <div className="flex items-center gap-2 rounded-xl bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
                      <FileAudio size={17} className="text-violet-500" />
                      Audio upload
                    </div>

                    <div className="flex items-center gap-2 rounded-xl bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
                      <AudioLines size={17} className="text-blue-500" />
                      Microphone recording
                    </div>
                  </div>

                  <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-400">
                    <CheckCircle2 size={14} className="text-emerald-500" />
                    AI-assisted analysis · Human review · Editable DOCX
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Workflow introduction */}
        <section className="mt-8 grid gap-4 md:grid-cols-3">
          {/* Transcription */}
          <div className="surface p-5">
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
              <AudioLines size={18} />
            </div>

            <h3 className="font-semibold text-slate-900">01 · Transcribe</h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Convert your audio into text using speech recognition.
            </p>
          </div>

          {/* AI structuring */}
          <div className="surface p-5">
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
              <Sparkles size={18} />
            </div>

            <h3 className="font-semibold text-slate-900">
              02 · Structure with AI
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Identify definitions, headings, examples, paragraphs, and more.
            </p>
          </div>

          {/* Review and export */}
          <div className="surface p-5">
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
              <CheckCircle2 size={18} />
            </div>

            <h3 className="font-semibold text-slate-900">
              03 · Review & export
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Confirm the structure and generate your editable Word document.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}

export default App;