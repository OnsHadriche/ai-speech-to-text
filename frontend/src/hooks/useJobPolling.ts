import { useEffect, useState } from "react";
import { getJob } from "../services/jobs";
import type { JobResponse } from "../services/jobs";

interface UseJobPollingOptions {
  jobId: string | null;
  enabled?: boolean;
  interval?: number;
}

export default function useJobPolling({
  jobId,
  enabled = true,
  interval = 2000,
}: UseJobPollingOptions) {
  const [job, setJob] = useState<JobResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!jobId || !enabled) {
      return;
    }

    let isActive = true;
    let timeoutId: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const currentJob = await getJob(jobId!);

        if (!isActive) return;

        setJob(currentJob);

        const isFinished = [
          "transcribed",
          "transcription_failed",
          "failed_permanently",
        ].includes(currentJob.status);

        if (isFinished) {
          setIsPolling(false);
          return;
        }

        timeoutId = setTimeout(poll, interval);
      } catch (err) {
        if (!isActive) return;

        setError(
          err instanceof Error
            ? err.message
            : "Unable to retrieve job status.",
        );

        setIsPolling(false);
      }
    }

    Promise.resolve().then(() => {
      if (!isActive) return;

      setIsPolling(true);
      setError(null);
      return poll();
    });

    return () => {
      isActive = false;
      clearTimeout(timeoutId);
    };
  }, [jobId, enabled, interval]);

  return {
    job,
    error,
    isPolling: Boolean(jobId && enabled && isPolling),
  };
}