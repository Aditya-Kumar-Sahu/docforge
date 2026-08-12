import type { Metadata } from "next";
import localFont from "next/font/local";
import { CSPostHogProvider } from './providers'
import "./globals.css";
import Link from 'next/link';

import NavAuth from '@/components/NavAuth';

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "DocForge",
  description: "AI-powered API documentation generator",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <CSPostHogProvider>
        <body
          className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-50 text-gray-900`}
        >
          <nav className="w-full border-b bg-white p-4 flex gap-6 items-center shadow-sm">
            <Link href="/" className="font-bold text-xl text-blue-600">DocForge</Link>
            <Link href="/repos" className="hover:text-blue-500 font-medium">Repos</Link>
            <div className="ml-auto">
              <NavAuth />
            </div>
          </nav>
          <main className="max-w-6xl mx-auto p-6 mt-4">
            {children}
          </main>
        </body>
      </CSPostHogProvider>
    </html>
  );
}
