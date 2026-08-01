import { useEffect, useState, useRef } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { supabase } from '@/lib/supabase';

export function useSSE<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      controllerRef.current = new AbortController();

      try {
        await fetchEventSource(url, {
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Accept': 'text/event-stream',
          },
          signal: controllerRef.current.signal,
          onopen: async (response) => {
            if (response.ok && response.headers.get('content-type')?.includes('text/event-stream')) {
              setIsConnected(true);
              setError(null);
            } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
              // Client-side errors, don't retry
              throw new Error(`SSE connection failed with status ${response.status}`);
            }
          },
          onmessage: (event) => {
            try {
              const parsedData = JSON.parse(event.data);
              setData(parsedData);
            } catch (e) {
              console.error("Failed to parse SSE data", e);
            }
          },
          onerror: (err) => {
            console.error("SSE Error:", err);
            setError(err);
            setIsConnected(false);
            // Throw to allow fetch-event-source to retry or stop
            throw err;
          },
          onclose: () => {
            setIsConnected(false);
          }
        });
      } catch (err: unknown) {
        const e = err as Error;
        if (e.name !== 'AbortError') {
          setError(e);
        }
      }
    };

    fetchData();

    return () => {
      if (controllerRef.current) {
        controllerRef.current.abort();
      }
      setIsConnected(false);
    };
  }, [url]);

  return { data, isConnected, error };
}
