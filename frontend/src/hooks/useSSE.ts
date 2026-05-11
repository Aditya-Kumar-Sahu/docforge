import { useState, useEffect } from "react";

export function useSSE<T>(url: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!url) return;

    setLoading(true);
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        setData(parsedData);
      } catch (err) {
        console.error("Failed to parse SSE data", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE connection error", err);
      setError(new Error("SSE connection failed"));
      eventSource.close();
      setLoading(false);
    };

    return () => {
      eventSource.close();
      setLoading(false);
    };
  }, [url]);

  return { data, error, loading };
}
