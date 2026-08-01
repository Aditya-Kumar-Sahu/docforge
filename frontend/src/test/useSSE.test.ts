/**
 * Tests for the useSSE hook.
 *
 * The hook depends on @microsoft/fetch-event-source and @/lib/supabase,
 * both of which are mocked below so we can verify the hook's state machine
 * without network access.
 */
import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("@/lib/supabase", () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: "test-token" } },
      }),
    },
  },
}));

let mockOnMessage: ((event: { data: string }) => void) | null = null;
let mockOnError: ((err: unknown) => void) | null = null;
let abortSignal: AbortSignal | null = null;

vi.mock("@microsoft/fetch-event-source", () => ({
  fetchEventSource: vi.fn(
    async (
      _url: string,
      opts: {
        onopen?: (res: Response) => Promise<void>;
        onmessage?: (event: { data: string }) => void;
        onerror?: (err: unknown) => void;
        onclose?: () => void;
        signal?: AbortSignal;
      }
    ) => {
      mockOnMessage = opts.onmessage ?? null;
      mockOnError = opts.onerror ?? null;
      abortSignal = opts.signal ?? null;

      // Simulate a successful open
      if (opts.onopen) {
        await opts.onopen(
          new Response(null, {
            status: 200,
            headers: { "content-type": "text/event-stream" },
          })
        );
      }
    }
  ),
}));

// ── Tests ──────────────────────────────────────────────────────────────────

import { useSSE } from "@/hooks/useSSE";

describe("useSSE", () => {
  beforeEach(() => {
    mockOnMessage = null;
    mockOnError = null;
    abortSignal = null;
  });

  it("starts disconnected and connects after mount", async () => {
    const { result } = renderHook(() => useSSE<{ status: string }>("/api/test"));
    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it("parses incoming JSON messages and exposes them as data", async () => {
    const { result } = renderHook(() => useSSE<{ status: string; progress: number }>("/api/test"));

    await waitFor(() => expect(result.current.isConnected).toBe(true));

    act(() => {
      mockOnMessage?.({ data: JSON.stringify({ status: "scanning", progress: 30 }) });
    });

    expect(result.current.data).toEqual({ status: "scanning", progress: 30 });
  });

  it("sets error state when SSE fires an error", async () => {
    const { result } = renderHook(() => useSSE("/api/test"));

    await waitFor(() => expect(result.current.isConnected).toBe(true));

    act(() => {
      try {
        mockOnError?.(new Error("connection dropped"));
      } catch {
        // hook re-throws — that is expected behaviour
      }
    });

    await waitFor(() => {
      expect(result.current.error).not.toBeNull();
    });
  });

  it("aborts the connection on unmount", async () => {
    const { result, unmount } = renderHook(() => useSSE("/api/test"));
    await waitFor(() => expect(result.current.isConnected).toBe(true));

    unmount();

    expect(abortSignal?.aborted).toBe(true);
  });

  it("does not throw on non-JSON SSE data", async () => {
    const { result } = renderHook(() => useSSE<string>("/api/test"));
    await waitFor(() => expect(result.current.isConnected).toBe(true));

    act(() => {
      mockOnMessage?.({ data: "not-json{{" });
    });

    // data stays null — no exception propagated
    expect(result.current.data).toBeNull();
  });
});
