import { useCallback, useState } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastMessage {
  id: number;
  message: string;
  type: ToastType;
}

export function useToast() {
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const showToast = useCallback(
    (message: string, type: ToastType = "success") => {
      setToast({
        id: Date.now(),
        message,
        type,
      });
    },
    []
  );

  const hideToast = useCallback(() => {
    setToast(null);
  }, []);

  return {
    toast,
    showToast,
    hideToast,
  };
}