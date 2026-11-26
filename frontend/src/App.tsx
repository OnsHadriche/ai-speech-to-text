import { useCallback, useState } from "react";
import {
  FileAudio,
  UploadCloud,
  AlertCircle,
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

function App() {
  // Application state
  const isBackendOnline = useBackendHealth();
  const { toast, showToast, hideToast } = useToast();

  const [selectedAudio, setSelectedAudio] = useState<File | null>(null);
  const [sourceType, setSourceType] =
    useState<AudioSourceType>("upload");

  const [audioInputKey, setAudioInputKey] = useState(0);

  // Upload workflow
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

  // Audio selection
  const handleAudioSelected = useCallback(
    (file: File | null, selectedSourceType: AudioSourceType) => {
      setSelectedAudio(file);
      setSourceType(selectedSourceType);

      resetUpload();
      hideToast();
    },
    [resetUpload, hideToast]
  );

  // Upload
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

  // Reset workflow
  const handleStartNewDocument = useCallback(() => {
    setSelectedAudio(null);
    setSourceType("upload");

    resetUpload();
    hideToast();

    setAudioInputKey((previousKey) => previousKey + 1);
  }, [resetUpload, hideToast]);

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
        {/* Hero */}
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
            {!uploadedJob ? (
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

                      <p className="mt-1">{uploadError}</p>
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
            ) : (
              /* Transcription workflow */
              <TranscriptionPanel
                job={uploadedJob}
                onStartNew={handleStartNewDocument}
              />
            )}
          </div>
        </Card>

        {/* Workflow information */}
        {!uploadedJob && <WorkflowOverview />}

        {/* Footer */}
        <AppFooter />
      </main>
    </AppLayout>
  );
}

export default App;