'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center px-4">
      {/* Hero */}
      <div className="mb-4 inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-sm font-medium px-3 py-1 rounded-full border border-blue-200">
        <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
        AI-powered API documentation
      </div>

      <h1 className="text-5xl font-extrabold text-gray-900 mb-4 leading-tight">
        Document your API in{' '}
        <span className="text-blue-600">minutes</span>, not days.
      </h1>

      <p className="text-lg text-gray-600 max-w-xl mb-8">
        DocForge parses your FastAPI codebase with AST analysis and uses AI to generate
        Stripe-quality OpenAPI 3.1 specs and Markdown docs — without touching a single decorator.
      </p>

      <div className="flex gap-4 flex-wrap justify-center">
        <Link
          href="/repos"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition shadow"
        >
          Connect a Repository →
        </Link>
        <Link
          href="/login"
          className="bg-white text-gray-700 border border-gray-300 px-6 py-3 rounded-lg font-semibold hover:bg-gray-50 transition"
        >
          Sign In
        </Link>
      </div>

      {/* Feature grid */}
      <div className="mt-20 grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-3xl w-full text-left">
        {[
          {
            icon: '🔍',
            title: 'AST Parsing',
            desc: 'tree-sitter extracts every route, param, and response model — no decorators required.',
          },
          {
            icon: '🤖',
            title: 'AI Generation',
            desc: 'Gemini Flash writes descriptions, examples, and error responses for each endpoint.',
          },
          {
            icon: '📄',
            title: 'OpenAPI 3.1 Export',
            desc: 'Download a valid spec in seconds. Import to Postman, Redoc, or Mintlify.',
          },
        ].map((f) => (
          <div key={f.title} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <div className="text-3xl mb-3">{f.icon}</div>
            <h3 className="font-semibold text-gray-900 mb-1">{f.title}</h3>
            <p className="text-sm text-gray-500">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
