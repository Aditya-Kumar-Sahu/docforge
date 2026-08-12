/**
 * Tests for the LoginPage component.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// Mock next/navigation — useRouter is not available outside the Next.js App Router context in jsdom
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  usePathname: () => "/login",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock Supabase auth UI components (they rely on browser APIs not available in jsdom)
vi.mock("@supabase/auth-ui-react", () => ({
  Auth: ({ providers }: { providers: string[] }) => (
    <div data-testid="supabase-auth-ui">
      {providers.map((p) => (
        <button key={p}>{p} login</button>
      ))}
    </div>
  ),
}));

vi.mock("@supabase/auth-ui-shared", () => ({
  ThemeSupa: {},
}));

vi.mock("@/lib/supabase", () => ({
  supabase: {
    auth: {
      getSession: vi.fn(() => Promise.resolve({ data: { session: null } })),
      onAuthStateChange: vi.fn(() => ({
        data: { subscription: { unsubscribe: vi.fn() } },
      })),
    },
  },
}));

vi.mock("posthog-js", () => ({
  default: { identify: vi.fn(), capture: vi.fn() },
}));

import LoginPage from "@/app/login/page";

describe("LoginPage", () => {
  it("renders the login heading", () => {
    render(<LoginPage />);
    expect(screen.getByRole("heading", { name: /login to docforge/i })).toBeInTheDocument();
  });

  it("renders the Supabase Auth UI component", () => {
    render(<LoginPage />);
    expect(screen.getByTestId("supabase-auth-ui")).toBeInTheDocument();
  });

  it("offers GitHub as a login provider", () => {
    render(<LoginPage />);
    expect(screen.getByText(/github login/i)).toBeInTheDocument();
  });
});
