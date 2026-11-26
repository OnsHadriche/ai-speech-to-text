import { useCallback, useState } from "react";
import {
  FileAudio,
  UploadCloud,
  AlertCircle,
  ArrowLeft,
  RefreshCw,
  CheckCircle2,
  X,
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
  CLASSIFICATION_OPTIONS,
  getClassificationLabel,
  type SegmentType,
} from "./constants/classification";

import {
  createDocument,
  analyzeDocument,
  getNextClassificationBatch,
} from "./services/documents";

import type {
  DocumentResponse,
  AnalyzeDocumentResponse,
  NextBatchResponse,
} from "./services/documents";

type WorkflowStep = "upload" | "transcription" | "structuring";

function App() {
  // ==========================================
  // Application state
  // ==========================================

  const isBackendOnline = useBackendHealth();
  const { toast, showToast, hideToast } = useToast();

  const [selectedAudio, setSelectedAudio] =
    useState<File | null>(null);

  const [sourceType, setSourceType] =
    useState<AudioSourceType>("upload");

  const [audioInputKey, setAudioInputKey] = useState(0);
  const [segmentSelections, setSegmentSelections] = useState<
    Record<string, SegmentType>
  >({});
  // ==========================================
  // Workflow state
  // ==========================================

  const [workflowStep, setWorkflowStep] =
    useState<WorkflowStep>("upload");

  const [transcript, setTranscript] = useState("");

  // ==========================================
  // Document analysis state
  // ==========================================

  const [document, setDocument] =
    useState<DocumentResponse | null>(null);

  const [analysisResult, setAnalysisResult] =
    useState<AnalyzeDocumentResponse | null>(null);

  const [currentBatch, setCurrentBatch] =
    useState<NextBatchResponse | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [isLoadingBatch, setIsLoadingBatch] = useState(false);

  const [analysisError, setAnalysisError] =
    useState<string | null>(null);

  const [batchError, setBatchError] =
    useState<string | null>(null);

  // ==========================================
  // Analysis details modal state
  // ==========================================

  const [isAnalysisDetailsOpen, setIsAnalysisDetailsOpen] =
    useState(false);

  // ==========================================
  // Upload workflow
  // ==========================================

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

  // ==========================================
  // Audio selection
  // ==========================================

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
      setCurrentBatch(null);

      setAnalysisError(null);
      setBatchError(null);
      setIsAnalysisDetailsOpen(false);
    },
    [resetUpload, hideToast]
  );

  // ==========================================
  // Upload audio
  // ==========================================

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

  // ==========================================
  // Continue to structuring
  // ==========================================

  const handleContinueToStructuring = useCallback(
    (editedTranscript: string) => {
      setTranscript(editedTranscript);
      setWorkflowStep("structuring");

      setDocument(null);
      setAnalysisResult(null);
      setCurrentBatch(null);

      setAnalysisError(null);
      setBatchError(null);
      setIsAnalysisDetailsOpen(false);
    },
    []
  );

  // ==========================================
  // Fetch classification batch
  // ==========================================

  const handleLoadBatch = useCallback(
    async (documentId: string) => {
      setIsLoadingBatch(true);
      setBatchError(null);

      try {
        const batchResult =
          await getNextClassificationBatch(documentId);

        setCurrentBatch(batchResult);

        return batchResult;
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Failed to load classification batch.";

        setBatchError(message);
        return null;
      } finally {
        setIsLoadingBatch(false);
      }
    },
    []
  );

  // ==========================================
  // Create document and analyze transcript
  // ==========================================

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
    setBatchError(null);
    setAnalysisResult(null);
    setCurrentBatch(null);
    setIsAnalysisDetailsOpen(false);
    setSegmentSelections({});

    try {
      // 1. Create document using reviewed transcript
      const createdDocument = await createDocument({
        job_id: uploadedJob.id,
        language: "ar",
        reviewed_transcript: transcript,
      });

      setDocument(createdDocument);

      // 2. Analyze document
      const result = await analyzeDocument(
        createdDocument.id,
        4
      );

      setAnalysisResult(result);

      // 3. Fetch the first classification batch
      await handleLoadBatch(createdDocument.id);

      // Use existing Toast UI
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
  }, [
    uploadedJob,
    transcript,
    showToast,
    handleLoadBatch,
  ]);

  // ==========================================
  // Retry loading batch
  // ==========================================

  const handleRetryBatch = useCallback(async () => {
    if (!document) {
      showToast("Document not found.", "error");
      return;
    }

    await handleLoadBatch(document.id);
  }, [document, handleLoadBatch, showToast]);

  // ==========================================
  // Back to transcription
  // ==========================================

  const handleBackToTranscription = useCallback(() => {
    setWorkflowStep("transcription");
    setIsAnalysisDetailsOpen(false);
  }, []);

  // ==========================================
  // Reset workflow
  // ==========================================

  const handleStartNewDocument = useCallback(() => {
    setSelectedAudio(null);
    setSourceType("upload");

    setTranscript("");

    setDocument(null);
    setAnalysisResult(null);
    setCurrentBatch(null);

    setIsAnalyzing(false);
    setIsLoadingBatch(false);

    setAnalysisError(null);
    setBatchError(null);
    setIsAnalysisDetailsOpen(false);

    setWorkflowStep("upload");

    resetUpload();
    hideToast();

    setSegmentSelections({});

    setAudioInputKey((previousKey) => previousKey + 1);
  }, [resetUpload, hideToast]);

  // ==========================================
  // Derived state
  // ==========================================

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
  
  const handleSegmentTypeChange = useCallback(
      (segmentId: string, selectedType: SegmentType) => {
        setSegmentSelections((previous) => ({
          ...previous,
          [segmentId]: selectedType,
        }));
      },
      []
    
    );

  // ==========================================
  // Render
  // ==========================================

  return (
    <AppLayout>
      {/* Existing Toast UI */}
      {toast && (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
        />
      )}

      <AppHeader isBackendOnline={isBackendOnline} />

      <main className="mx-auto max-w-7xl px-5 py-8 md:px-8">
        <HeroSection />

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
            {/* ====================================== */}
            {/* Upload phase                           */}
            {/* ====================================== */}

            {isUploadPhase && (
              <>
                <AudioInput
                  key={audioInputKey}
                  onFileSelected={handleAudioSelected}
                />

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

            {/* ====================================== */}
            {/* Transcription phase                     */}
            {/* ====================================== */}

            {isTranscriptionPhase && uploadedJob && (
              <TranscriptionPanel
                job={uploadedJob}
                onStartNewDocument={handleStartNewDocument}
                onContinueToStructuring={
                  handleContinueToStructuring
                }
              />
            )}

            {/* ====================================== */}
            {/* Structuring phase                       */}
            {/* ====================================== */}

            {isStructuringPhase && (
              <section className="space-y-5">
                {/* Structuring header */}
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

                {/* Transcript success */}
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
                  <h3 className="font-semibold text-emerald-900">
                    Transcript received successfully
                  </h3>

                  <p className="mt-1 text-sm text-emerald-700">
                    Your reviewed transcript is ready for AI analysis.
                  </p>
                </div>

                {/* Reviewed transcript */}
                <div className="rounded-xl border border-slate-200 bg-white p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="font-medium text-slate-900">
                      Reviewed Transcript
                    </h3>

                    <span className="text-xs text-slate-500">
                      {transcriptWordCount} words
                    </span>
                  </div>

                  <div
                    className="max-h-96 overflow-y-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-sm leading-7 text-slate-700"
                    dir="auto"
                  >
                    {transcript || "No transcript available."}
                  </div>
                </div>

                {/* ================================== */}
                {/* Analysis section                    */}
                {/* ================================== */}

                <div className="space-y-4">
                  {/* Before analysis */}
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

                  {/* ================================= */}
                  {/* Compact analysis summary            */}
                  {/* ================================= */}

                  {analysisResult && (
                    <div className="flex flex-col gap-4 rounded-xl border border-emerald-200 bg-emerald-50 p-5 sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex items-start gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                          <CheckCircle2 size={20} />
                        </div>

                        <div>
                          <h3 className="font-semibold text-emerald-900">
                            Analysis completed
                          </h3>

                          <p className="mt-1 text-sm text-emerald-700">
                            {analysisResult.total_segments} segments analyzed ·{" "}
                            {analysisResult.total_batches} batches created
                          </p>
                        </div>
                      </div>

                      <Button
                        variant="secondary"
                        onClick={() =>
                          setIsAnalysisDetailsOpen(true)
                        }
                      >
                        View Details
                      </Button>
                    </div>
                  )}

                  {/* ================================= */}
                  {/* Analysis details modal             */}
                  {/* ================================= */}

                  {analysisResult && isAnalysisDetailsOpen && (
                    <div
                      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
                      onClick={() =>
                        setIsAnalysisDetailsOpen(false)
                      }
                    >
                      <div
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="analysis-modal-title"
                        className="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl"
                        onClick={(event) =>
                          event.stopPropagation()
                        }
                      >
                        {/* Modal header */}
                        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
                          <div>
                            <h2
                              id="analysis-modal-title"
                              className="text-lg font-semibold text-slate-900"
                            >
                              Analysis Details
                            </h2>

                            <p className="mt-1 text-sm text-slate-500">
                              Details about your analyzed document.
                            </p>
                          </div>

                          <button
                            type="button"
                            onClick={() =>
                              setIsAnalysisDetailsOpen(false)
                            }
                            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
                            aria-label="Close analysis details"
                          >
                            <X size={18} />
                          </button>
                        </div>

                        {/* Modal content */}
                        <div className="max-h-[75vh] space-y-5 overflow-y-auto p-6">
                          {/* Statistics */}
                          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                              <p className="text-xs text-slate-500">
                                Total Segments
                              </p>

                              <p className="mt-2 text-2xl font-semibold text-slate-900">
                                {analysisResult.total_segments}
                              </p>
                            </div>

                            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                              <p className="text-xs text-slate-500">
                                Classification Batches
                              </p>

                              <p className="mt-2 text-2xl font-semibold text-slate-900">
                                {analysisResult.total_batches}
                              </p>
                            </div>

                            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                              <p className="text-xs text-slate-500">
                                Document Type
                              </p>

                              <p className="mt-2 text-sm font-semibold capitalize text-slate-900">
                                {analysisResult.document.document_type ||
                                  "Not detected"}
                              </p>
                            </div>
                          </div>

                          {/* Document information */}
                          <div className="rounded-xl border border-slate-200 p-4">
                            <h3 className="font-medium text-slate-900">
                              Document Information
                            </h3>

                            <div className="mt-4 space-y-3 text-sm">
                              <div>
                                <p className="text-slate-500">
                                  Document ID
                                </p>

                                <p className="mt-1 break-all font-medium text-slate-900">
                                  {document?.id ?? "—"}
                                </p>
                              </div>

                              <div>
                                <p className="text-slate-500">
                                  Title
                                </p>

                                <p className="mt-1 font-medium text-slate-900">
                                  {analysisResult.document.title ||
                                    "Not detected"}
                                </p>
                              </div>

                              <div>
                                <p className="text-slate-500">
                                  Subject
                                </p>

                                <p className="mt-1 font-medium text-slate-900">
                                  {analysisResult.document.subject ||
                                    "Not detected"}
                                </p>
                              </div>

                              <div>
                                <p className="text-slate-500">
                                  Topic
                                </p>

                                <p className="mt-1 font-medium text-slate-900">
                                  {analysisResult.document.topic ||
                                    "Not detected"}
                                </p>
                              </div>

                              <div>
                                <p className="text-slate-500">
                                  Status
                                </p>

                                <span className="mt-1 inline-flex rounded-full bg-violet-100 px-3 py-1 text-xs font-medium capitalize text-violet-700">
                                  {analysisResult.document.status.replaceAll(
                                    "_",
                                    " "
                                  )}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Batch information */}
                          <div className="rounded-xl border border-slate-200 p-4">
                            <h3 className="font-medium text-slate-900">
                              Classification Batches
                            </h3>

                            <div className="mt-3 space-y-2">
                              {analysisResult.batches.map(
                                (batch) => (
                                  <div
                                    key={batch.id}
                                    className="flex items-center justify-between rounded-lg border border-slate-200 p-3"
                                  >
                                    <span className="text-sm font-medium text-slate-700">
                                      Batch {batch.batch_number}
                                    </span>

                                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs capitalize text-slate-600">
                                      {batch.status.replaceAll(
                                        "_",
                                        " "
                                      )}
                                    </span>
                                  </div>
                                )
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Modal footer */}
                        <div className="flex justify-end border-t border-slate-200 bg-slate-50 px-6 py-4">
                          <Button
                            variant="secondary"
                            onClick={() =>
                              setIsAnalysisDetailsOpen(false)
                            }
                          >
                            Close
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* ================================= */}
                  {/* Batch loading                     */}
                  {/* ================================= */}

                  {analysisResult && isLoadingBatch && (
                    <div className="rounded-xl border border-slate-200 bg-white p-6">
                      <div className="flex items-center justify-center gap-3">
                        <RefreshCw
                          size={18}
                          className="animate-spin text-violet-600"
                        />

                        <p className="text-sm text-slate-600">
                          Loading classification batch...
                        </p>
                      </div>
                    </div>
                  )}

                  {/* ================================= */}
                  {/* Batch error                       */}
                  {/* ================================= */}

                  {analysisResult && batchError && (
                    <div className="rounded-xl border border-red-200 bg-red-50 p-5">
                      <div className="flex items-start gap-3">
                        <AlertCircle
                          size={18}
                          className="mt-0.5 text-red-600"
                        />

                        <div className="flex-1">
                          <h3 className="font-semibold text-red-900">
                            Failed to load classification batch
                          </h3>

                          <p className="mt-1 text-sm text-red-700">
                            {batchError}
                          </p>

                          <div className="mt-4">
                            <Button
                              variant="secondary"
                              loading={isLoadingBatch}
                              loadingText="Retrying..."
                              disabled={isLoadingBatch}
                              onClick={handleRetryBatch}
                            >
                              Retry
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* ================================= */}
                  {/* Segment review                     */}
                  {/* ================================= */}

                  {analysisResult &&
                    currentBatch &&
                    !isLoadingBatch && (
                      <div className="space-y-4">
                        {/* Batch header */}
                        <div className="rounded-xl border border-violet-200 bg-violet-50 p-5">
                          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                            <div>
                              <h3 className="font-semibold text-violet-900">
                                Segment Review
                              </h3>

                              <p className="mt-1 text-sm text-violet-700">
                                Review the AI suggestions for each segment.
                              </p>
                            </div>

                            {currentBatch.batch && (
                              <span className="rounded-full bg-white px-3 py-1.5 text-sm font-medium text-violet-700">
                                Batch{" "}
                                {currentBatch.batch.batch_number}
                              </span>
                            )}
                          </div>

                          {currentBatch.batch && (
                            <div className="mt-4 flex flex-wrap gap-3">
                              <span className="rounded-lg bg-white px-3 py-2 text-sm text-slate-700">
                                {currentBatch.segments.length} segments
                              </span>

                              <span className="rounded-lg bg-white px-3 py-2 text-sm text-slate-700">
                                Status: {currentBatch.batch.status}
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Empty batch */}
                        {!currentBatch.batch && (
                          <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
                            <h3 className="font-semibold text-slate-900">
                              No classification batches available
                            </h3>

                            <p className="mt-2 text-sm text-slate-500">
                              There are currently no segments waiting for review.
                            </p>
                          </div>
                        )}

                        {/* Segments */}
                        {currentBatch.segments.length > 0 && (
                          <div className="space-y-4">
                            {currentBatch.segments.map(
                              (segment) => (
                                <div
                                  key={segment.id}
                                  className="overflow-hidden rounded-xl border border-slate-200 bg-white"
                                >
                                  {/* Segment header */}
                                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3">
                                    <div className="flex items-center gap-2">
                                      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-100 text-sm font-semibold text-violet-700">
                                        {segment.position}
                                      </span>

                                      <div>
                                        <p className="text-sm font-medium text-slate-900">
                                          Segment {segment.position}
                                        </p>

                                        <p className="text-xs capitalize text-slate-500">
                                          {segment.classification_status.replaceAll(
                                            "_",
                                            " "
                                          )}
                                        </p>
                                      </div>
                                    </div>

                                    {segment.suggested_type && (
                                      <span className="rounded-full bg-violet-100 px-3 py-1.5 text-xs font-medium text-violet-700">
                                        AI:{" "}
                                        {segment.suggested_type.replaceAll(
                                          "_",
                                          " "
                                        )}
                                      </span>
                                    )}
                                  </div>

                                  {/* Segment content */}
                                  <div className="space-y-4 p-4">
                                    <div>
                                      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
                                        Segment Content
                                      </p>

                                      <div
                                        className="rounded-lg border border-slate-100 bg-slate-50 p-4 text-sm leading-8 text-slate-800"
                                        dir="auto"
                                      >
                                        {segment.original_text}
                                      </div>
                                    </div>

                                    {/* Confidence and selected type */}
                                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                      {segment.suggestion_confidence !==
                                        null &&
                                        segment.suggestion_confidence !==
                                          undefined && (
                                          <div className="rounded-lg border border-slate-100 p-3">
                                            <p className="text-xs text-slate-500">
                                              AI Confidence
                                            </p>

                                            <p className="mt-1 font-semibold text-slate-900">
                                              {Math.round(
                                                segment.suggestion_confidence *
                                                  100
                                              )}
                                              %
                                            </p>

                                            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                                              <div
                                                className="h-full rounded-full bg-violet-500"
                                                style={{
                                                  width: `${Math.max(
                                                    0,
                                                    Math.min(
                                                      100,
                                                      segment.suggestion_confidence *
                                                        100
                                                    )
                                                  )}%`,
                                                }}
                                              />
                                            </div>
                                          </div>
                                        )}
                                        <div className="rounded-lg border border-slate-100 p-3">
                                        <label
                                          htmlFor={`classification-${segment.id}`}
                                          className="text-xs font-medium text-slate-500"
                                        >
                                          Classification
                                        </label>

                                        <select
                                          id={`classification-${segment.id}`}
                                          value={
                                            segmentSelections[segment.id] ??
                                            segment.selected_type ??
                                            segment.suggested_type ??
                                            ""
                                          }
                                          onChange={(event) =>
                                            handleSegmentTypeChange(
                                              segment.id,
                                              event.target.value as SegmentType
                                            )
                                          }
                                          className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900 outline-none transition focus:border-violet-500 focus:ring-2 focus:ring-violet-100"
                                        >
                                          <option value="" disabled>
                                            Select classification
                                          </option>

                                          {CLASSIFICATION_OPTIONS.map((option) => (
                                            <option
                                              key={option.value}
                                              value={option.value}
                                            >
                                              {option.label}
                                            </option>
                                          ))}
                                        </select>

                                        <p className="mt-2 text-xs text-slate-400">
                                          Review the AI suggestion or choose another classification.
                                        </p>
                                      </div>
                                    </div>

                                    {/* AI reasoning */}
                                    {segment.suggestion_reason && (
                                      <div className="rounded-lg border border-blue-100 bg-blue-50 p-3">
                                        <p className="text-xs font-medium text-blue-800">
                                          AI Reasoning
                                        </p>

                                        <p className="mt-1 text-sm leading-6 text-blue-700">
                                          {segment.suggestion_reason}
                                        </p>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        )}
                      </div>
                    )}
                </div>
              </section>
            )}
          </div>
        </Card>

        {/* Workflow overview */}
        {isUploadPhase && <WorkflowOverview />}

        {/* Footer */}
        <AppFooter />
      </main>
    </AppLayout>
  );
}

export default App;