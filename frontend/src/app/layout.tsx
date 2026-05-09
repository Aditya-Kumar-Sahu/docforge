import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "DocForge",
  description: "AI-powered API documentation platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <nav className="border-b bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <div className="flex items-center">
                <Link href="/" className="text-xl font-bold text-blue-600">
                  DocForge
                </Link>
                <div className="ml-10 flex items-baseline space-x-4">
                  <Link href="/repos" className="hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium">
                    Repos
                  </Link>
                  <Link href="/docs" className="hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium">
                    Docs
                  </Link>
                </div>
              </div>
              <div>
                <Link href="/login" className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {children}
        </main>
      </body>
    </html>
  );
}
