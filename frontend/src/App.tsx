import { useCallback, useState } from "react";
import {
  FileAudio,
  UploadCloud,
  AlertCircle,
  ArrowLeft,
} from "lucide-react";

import AppLayout from "./components/layout/AppLayout";
import AppHeader from "./components/layout/AppHeader";
import HeroSection from "./components/layout/HeroSection";
import WorkflowOverview from "./components/layout/WorkflowOverview";
import AppFooter from "./components/layout/AppFooter";

import AudioInput from "./components/audio/AudioInput";
import TranscriptionPanel from "./components/transcription/TranscriptionPanel";

import Button from "./components/ui/Button";
import Card from "./components/ui/Card";
import Toast from "./components/ui/Toast";

import { useBackendHealth } from "./hooks/useBackendStatus";
import { useToast } from "./hooks/useToast";
import { useAudioUpload } from "./hooks/useAudioUpload";

import type { AudioSourceType } from "./services/jobs";

import {
  createDocument,
  analyzeDocument,
} from "./services/documents";

import type {
  DocumentResponse,
  AnalyzeDocumentResponse,
} from "./services/documents";

type WorkflowStep = "upload" | "transcription" | "structuring";

function App() {
  // --------------------------------------------------
  // Application state
  // --------------------------------------------------

  const isBackendOnline = useBackendHealth();

  const { toast, showToast, hideToast } = useToast();

  const [selectedAudio, setSelectedAudio] =
    useState<File | null>(null);

  const [sourceType, setSourceType] =
    useState<AudioSourceType>("upload");

  const [audioInputKey, setAudioInputKey] =
    useState(0);

  // --------------------------------------------------
  // Workflow state
  // --------------------------------------------------

  const [workflowStep, setWorkflowStep] =
    useState<WorkflowStep>("upload");

  const [transcript, setTranscript] = useState("");

  // --------------------------------------------------
  // Document analysis state
  // --------------------------------------------------

  const [document, setDocument] =
    useState<DocumentResponse | null>(null);

  const [analysisResult, setAnalysisResult] =
    useState<AnalyzeDocumentResponse | null>(null);

  const [isAnalyzing, setIsAnalyzing] =
    useState(false);

  const [analysisError, setAnalysisError] =
    useState<string | null>(null);

  // --------------------------------------------------
  // Upload workflow
  // --------------------------------------------------

  const handleUploadSuccess = useCallback(() => {
    showToast("Audio uploaded successfully.", "success");
  }, [showToast]);

  const {
    upload,
    job: uploadedJob,
    error: uploadError,
    isUploading,
    reset: resetUpload,
  } = useAudioUpload({
    isBackendOnline,
    onSuccess: handleUploadSuccess,
  });

  // --------------------------------------------------
  // Audio selection
  // --------------------------------------------------

  const handleAudioSelected = useCallback(
    (
      file: File | null,
      selectedSourceType: AudioSourceType
    ) => {
      setSelectedAudio(file);
      setSourceType(selectedSourceType);

      resetUpload();
      hideToast();

      setWorkflowStep("upload");
      setTranscript("");

      setDocument(null);
      setAnalysisResult(null);
      setAnalysisError(null);
    },
    [resetUpload, hideToast]
  );

  // --------------------------------------------------
  // Upload audio
  // --------------------------------------------------

  const handleUploadAudio = useCallback(async () => {
    if (!selectedAudio) {
      showToast(
        "Please select or record an audio file first.",
        "warning"
      );

      return;
    }

    await upload(selectedAudio, sourceType);
  }, [selectedAudio, sourceType, upload, showToast]);

  // --------------------------------------------------
  // Continue to structuring
  // --------------------------------------------------

  const handleContinueToStructuring = useCallback(
    (editedTranscript: string) => {
      setTranscript(editedTranscript);
      setWorkflowStep("structuring");

      setDocument(null);
      setAnalysisResult(null);
      setAnalysisError(null);
    },
    []
  );

  // --------------------------------------------------
  // Create document and analyze transcript
  // --------------------------------------------------

  const handleAnalyzeTranscript = useCallback(async () => {
    if (!uploadedJob) {
      showToast("No transcription job found.", "error");
      return;
    }

    if (!transcript.trim()) {
      showToast("The transcript is empty.", "warning");
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisResult(null);

    try {
      // 1. Create document using reviewed transcript
      const createdDocument = await createDocument({
        job_id: uploadedJob.id,
        language: "ar",
        reviewed_transcript: transcript,
      });

      setDocument(createdDocument);

      // 2. Trigger AI analysis
      const result = await analyzeDocument(
        createdDocument.id,
        4
      );

      setAnalysisResult(result);

      showToast(
        "AI analysis completed successfully.",
        "success"
      );
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to analyze transcript.";

      setAnalysisError(message);

      showToast(message, "error");
    } finally {
      setIsAnalyzing(false);
    }
  }, [uploadedJob, transcript, showToast]);

  // --------------------------------------------------
  // Return to transcription
  // --------------------------------------------------

  const handleBackToTranscription = useCallback(() => {
    setWorkflowStep("transcription");
  }, []);

  // --------------------------------------------------
  // Reset workflow
  // --------------------------------------------------

  const handleStartNewDocument = useCallback(() => {
    setSelectedAudio(null);
    setSourceType("upload");

    setTranscript("");

    setDocument(null);
    setAnalysisResult(null);
    setIsAnalyzing(false);
    setAnalysisError(null);

    setWorkflowStep("upload");

    resetUpload();
    hideToast();

    setAudioInputKey((previousKey) => previousKey + 1);
  }, [resetUpload, hideToast]);

  // --------------------------------------------------
  // Derived state
  // --------------------------------------------------

  const isUploadPhase =
    !uploadedJob && workflowStep === "upload";

  const isTranscriptionPhase =
    Boolean(uploadedJob) && workflowStep !== "structuring";

  const isStructuringPhase =
    workflowStep === "structuring";

  const transcriptWordCount = transcript
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;

  // --------------------------------------------------
  // Render
  // --------------------------------------------------

  return (
    <AppLayout>
      {/* Global notification */}
      {toast && (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
        />
      )}

      {/* Application header */}
      <AppHeader isBackendOnline={isBackendOnline} />

      <main className="mx-auto max-w-7xl px-5 py-8 md:px-8">
        {/* Hero section */}
        <HeroSection />

        {/* Main workflow */}
        <Card className="overflow-hidden">
          {/* Workflow header */}
          <div className="flex items-center gap-3 border-b border-slate-100 px-5 py-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
              <FileAudio size={18} />
            </div>

            <div>
              <h3 className="font-semibold text-slate-900">
                Create a new document
              </h3>

              <p className="mt-0.5 text-xs text-slate-500">
                Start with an audio recording or an existing audio file.
              </p>
            </div>
          </div>

          <div className="space-y-6 p-5 md:p-6">
            {/* ======================================== */}
            {/* Upload phase                             */}
            {/* ======================================== */}

            {isUploadPhase && (
              <>
                {/* Audio selection */}
                <AudioInput
                  key={audioInputKey}
                  onFileSelected={handleAudioSelected}
                />

                {/* Upload error */}
                {uploadError && (
                  <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                    <AlertCircle
                      size={18}
                      className="mt-0.5 shrink-0"
                    />

                    <div>
                      <p className="font-semibold">
                        Upload failed
                      </p>

                      <p className="mt-1">
                        {uploadError}
                      </p>
                    </div>
                  </div>
                )}

                {/* Upload action */}
                <div className="flex justify-end border-t border-slate-100 pt-5">
                  <Button
                    loading={isUploading}
                    loadingText="Uploading audio..."
                    icon={<UploadCloud size={17} />}
                    disabled={
                      !selectedAudio ||
                      isUploading ||
                      isBackendOnline !== true
                    }
                    onClick={handleUploadAudio}
                  >
                    Upload & Continue
                  </Button>
                </div>
              </>
            )}

            {/* ======================================== */}
            {/* Transcription phase                      */}
            {/* ======================================== */}

            {isTranscriptionPhase && uploadedJob && (
              <TranscriptionPanel
                job={uploadedJob}
                onStartNewDocument={handleStartNewDocument}
                onContinueToStructuring={
                  handleContinueToStructuring
                }
              />
            )}

            {/* ======================================== */}
            {/* Structuring phase                       */}
            {/* ======================================== */}

            {isStructuringPhase && (
              <section className="space-y-5">
                {/* Header */}
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-900">
                      AI Structuring
                    </h2>

                    <p className="mt-1 text-sm text-slate-500">
                      Analyze and organize your transcript into a structured document.
                    </p>
                  </div>

                  <Button
                    variant="secondary"
                    icon={<ArrowLeft size={16} />}
                    onClick={handleBackToTranscription}
                    disabled={isAnalyzing}
                  >
                    Back to Transcription
                  </Button>
                </div>

                {/* Transcript success message */}
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
                  <h3 className="font-semibold text-emerald-900">
                    Transcript received successfully
                  </h3>

                  <p className="mt-1 text-sm text-emerald-700">
                    Your reviewed transcript is ready for AI analysis.
                  </p>
                </div>

                {/* Transcript preview */}
                <div className="rounded-xl border border-slate-200 bg-white p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="font-medium text-slate-900">
                      Reviewed Transcript
                    </h3>

                    <span className="text-xs text-slate-500">
                      {transcriptWordCount} words
                    </span>
                  </div>

                  <div className="max-h-96 overflow-y-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-sm leading-7 text-slate-700">
                    {transcript || "No transcript available."}
                  </div>
                </div>

                {/* ==================================== */}
                {/* AI Analysis                           */}
                {/* ==================================== */}

                <div className="space-y-4">
                  {!analysisResult && (
                    <div className="rounded-xl border border-violet-200 bg-violet-50/50 p-6">
                      <div className="text-center">
                        <h3 className="font-semibold text-slate-900">
                          Ready to analyze your transcript?
                        </h3>

                        <p className="mx-auto mt-2 max-w-lg text-sm text-slate-500">
                          AI will analyze your reviewed transcript,
                          identify the document structure, detect
                          titles and content types, and organize
                          the segments into classification batches.
                        </p>
                      </div>

                      {/* Error message */}
                      {analysisError && (
                        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                          <p className="font-semibold">
                            Analysis failed
                          </p>

                          <p className="mt-1">
                            {analysisError}
                          </p>
                        </div>
                      )}

                      {/* Analyze button */}
                      <div className="mt-5 flex justify-center">
                        <Button
                          loading={isAnalyzing}
                          loadingText="Analyzing transcript..."
                          disabled={isAnalyzing}
                          onClick={handleAnalyzeTranscript}
                        >
                          Analyze Transcript with AI
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* ================================== */}
                  {/* Analysis success                    */}
                  {/* ================================== */}

                  {analysisResult && (
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
                      <h3 className="font-semibold text-emerald-900">
                        AI analysis completed successfully
                      </h3>

                      <p className="mt-1 text-sm text-emerald-700">
                        Your transcript has been analyzed and organized
                        into document segments.
                      </p>

                      {/* Statistics */}
                      <div className="mt-4 grid grid-cols-1 gap-3 ">
                        <div className="rounded-lg bg-white p-4">
                          <p>
                            <span className="text-slate-500">
                              Status:
                            </span>{" "}
                            {analysisResult.document.status}
                          </p>
                        </div>

          
                        </div>
                      </div>

                    

          
      
                  )}
                </div>
              </section>
            )}
          </div>
        </Card>

        {/* Workflow information */}
        {isUploadPhase && <WorkflowOverview />}

        {/* Footer */}
        <AppFooter />
      </main>
    </AppLayout>
  );
}

export default App;