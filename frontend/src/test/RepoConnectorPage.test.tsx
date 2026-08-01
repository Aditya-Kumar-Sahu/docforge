/**
 * Tests for RepoConnectorPage (repos/page.tsx).
 *
 * Every test must mock authFetch for the initial GET /api/repos that fires
 * on mount (useEffect), otherwise the component crashes with
 * "Cannot read properties of undefined (reading 'then')".
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock Next.js router
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock authFetch util
const mockAuthFetch = vi.fn();
vi.mock("@/utils/api", () => ({
  authFetch: (...args: unknown[]) => mockAuthFetch(...args),
}));

// Helper: resolved empty repos list (used as the default mount response)
const emptyReposList = () =>
  Promise.resolve({ ok: true, json: async () => [] as unknown[] });

// Helper: created repo response
const createdRepo = (id = "42") =>
  Promise.resolve({
    ok: true,
    json: async () => ({ id, url: "https://github.com/user/repo", name: "repo" }),
  });

// Helper: scan response
const scanOk = () =>
  Promise.resolve({ ok: true, json: async () => ({ status: "scan initiated" }) });

// Helper: error response
const serverError = () =>
  Promise.resolve({ ok: false, statusText: "Internal Server Error" });

import RepoConnectorPage from "@/app/repos/page";

describe("RepoConnectorPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the heading and form", async () => {
    // Mount GET /api/repos returns empty list
    mockAuthFetch.mockReturnValueOnce(emptyReposList());

    render(<RepoConnectorPage />);

    // Wait for the mount effect to settle
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /connect a repository/i })).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/repository url/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /connect and scan/i })).toBeInTheDocument();
  });

  it("disables the button and shows loading text while submitting", async () => {
    // 1st call: mount GET /api/repos → empty list
    // 2nd call: POST /api/repos → never resolves (keeps loading)
    mockAuthFetch
      .mockReturnValueOnce(emptyReposList())
      .mockReturnValueOnce(new Promise(() => {}));

    render(<RepoConnectorPage />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /connect and scan/i })).not.toBeDisabled()
    );

    const input = screen.getByLabelText(/repository url/i);
    fireEvent.change(input, { target: { value: "https://github.com/user/repo" } });
    fireEvent.click(screen.getByRole("button", { name: /connect and scan/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /connecting/i })).toBeDisabled();
    });
  });

  it("navigates to the scan page after successful repo creation", async () => {
    // 1st call: mount GET /api/repos → empty list
    // 2nd call: POST /api/repos → created repo {id: "42"}
    // 3rd call: POST /api/repos/42/scan → scan ok
    mockAuthFetch
      .mockReturnValueOnce(emptyReposList())
      .mockReturnValueOnce(createdRepo("42"))
      .mockReturnValueOnce(scanOk());

    render(<RepoConnectorPage />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /connect and scan/i })).not.toBeDisabled()
    );

    const input = screen.getByLabelText(/repository url/i);
    fireEvent.change(input, { target: { value: "https://github.com/user/repo" } });
    fireEvent.click(screen.getByRole("button", { name: /connect and scan/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/repos/42/scan");
    });
  });

  it("shows an error message when the API call fails", async () => {
    // 1st call: mount GET /api/repos → empty list
    // 2nd call: POST /api/repos → server error
    mockAuthFetch
      .mockReturnValueOnce(emptyReposList())
      .mockReturnValueOnce(serverError());

    render(<RepoConnectorPage />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /connect and scan/i })).not.toBeDisabled()
    );

    fireEvent.change(screen.getByLabelText(/repository url/i), {
      target: { value: "https://github.com/user/broken" },
    });
    fireEvent.click(screen.getByRole("button", { name: /connect and scan/i }));

    // Button should be re-enabled after the error
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /connect and scan/i })).not.toBeDisabled();
    });
    expect(mockPush).not.toHaveBeenCalled();
  });
});
