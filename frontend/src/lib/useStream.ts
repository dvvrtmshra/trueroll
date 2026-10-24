import { useEffect, useRef } from "react";
import api from "./api";
import { useAuthStore } from "../store/auth";

export interface StreamEvent {
  type: string;
  [key: string]: unknown;
}

export function useStream(onEvent: (e: StreamEvent) => void) {
  const token = useAuthStore((s) => s.token);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!token) return;
    let es: EventSource | null = null;
    let pollTimer: ReturnType<typeof setInterval> | null = null;

    function connectSSE() {
      es = new EventSource(`/api/stream?token=${token}`);
      es.onmessage = (e) => {
        try { onEventRef.current(JSON.parse(e.data)); } catch { /* ignore malformed */ }
      };
      es.onerror = () => {
        es?.close();
        es = null;
        startPolling();
      };
    }

    function startPolling() {
      pollTimer = setInterval(async () => {
        try {
          const res = await api.get<StreamEvent[]>("/activity?limit=3");
          for (const item of res.data) {
            const { type: _t, ...rest } = item;
            onEventRef.current({ type: "activity", ...rest });
          }
        } catch { /* ignore network errors */ }
      }, 5000);
    }

    connectSSE();
    return () => {
      es?.close();
      if (pollTimer) clearInterval(pollTimer);
    };
  }, [token]);
}
