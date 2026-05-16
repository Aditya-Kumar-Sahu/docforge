import { useEffect, useState } from 'react';

export function useSSE<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Event | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    eventSource.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        setData(parsedData);
      } catch (e) {
        console.error("Failed to parse SSE data", e);
      }
    };

    eventSource.onerror = (event) => {
      setIsConnected(false);
      setError(event);
      eventSource.close();
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [url]);

  return { data, isConnected, error };
}
