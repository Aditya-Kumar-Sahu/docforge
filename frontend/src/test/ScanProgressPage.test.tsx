/**
 * Tests for the ScanProgressPage component.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "7" }),
}));

vi.mock("@/utils/api", () => ({
  authFetch: vi.fn().mockResolvedValue({ ok: false }),
}));

// Default: connected, no data yet
type SSEResult = { data: unknown; isConnected: boolean; error: Error | null };
const mockUseSSE = vi.fn<() => SSEResult>(() => ({ data: null, isConnected: false, error: null }));
vi.mock("@/hooks/useSSE", () => ({
  useSSE: () => mockUseSSE(),
}));

import ScanProgressPage from "@/app/repos/[id]/scan/page";

describe("ScanProgressPage", () => {
  it("renders the scanning heading", () => {
    render(<ScanProgressPage />);
    expect(screen.getByRole("heading", { name: /scanning repository/i })).toBeInTheDocument();
  });

  it("shows zero percent progress bar when no data", () => {
    render(<ScanProgressPage />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveStyle({ width: "0%" });
  });

  it("reflects progress from SSE data", () => {
    mockUseSSE.mockReturnValue({
      data: { status: "parsing_ast", progress: 30 },
      isConnected: true,
      error: null,
    });

    render(<ScanProgressPage />);
    expect(screen.getByRole("progressbar")).toHaveStyle({ width: "30%" });
    expect(screen.getByText(/parsing_ast/i)).toBeInTheDocument();
  });

  it("shows 100% progress when completed", () => {
    mockUseSSE.mockReturnValue({
      data: { status: "completed", progress: 100 },
      isConnected: false,
      error: null,
    });

    render(<ScanProgressPage />);
    expect(screen.getByRole("progressbar")).toHaveStyle({ width: "100%" });
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });

  it("shows error banner when SSE errors and no fallback data", () => {
    mockUseSSE.mockReturnValue({
      data: null,
      isConnected: false,
      error: new Error("connection refused"),
    });

    render(<ScanProgressPage />);
    expect(screen.getByText(/error connecting/i)).toBeInTheDocument();
  });
});
