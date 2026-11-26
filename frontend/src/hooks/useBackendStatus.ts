import { useEffect, useState } from "react";

const API_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function useBackendHealth() {
  const [isBackendOnline, setIsBackendOnline] = useState<boolean | null>(
    null
  );

  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const response = await fetch(`${API_URL}/api/health`);

        setIsBackendOnline(response.ok);
      } catch {
        setIsBackendOnline(false);
      }
    };

    checkBackendHealth();
  }, []);

  return isBackendOnline;
}