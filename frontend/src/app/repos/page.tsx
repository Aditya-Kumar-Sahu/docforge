'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authFetch } from '@/utils/api';

interface Repo {
  id: string;
  url: string;
  name: string;
}

export default function RepoConnectorPage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [repos, setRepos] = useState<Repo[]>([]);
  const [fetchingRepos, setFetchingRepos] = useState(true);
  const router = useRouter();

  // Fetch existing repos on mount
  useEffect(() => {
    authFetch('/api/repos')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch repos');
        return res.json();
      })
      .then((data: Repo[]) => setRepos(data))
      .catch((err) => console.error('Failed to load repos:', err))
      .finally(() => setFetchingRepos(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await authFetch('/api/repos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) {
        throw new Error(`Failed to connect repo: ${res.statusText}`);
      }

      const data: Repo = await res.json();

      // Show the new repo card before navigating
      setRepos((prev) => [data, ...prev]);
      setUrl('');

      if (data.id) {
        await authFetch(`/api/repos/${data.id}/scan`, { method: 'POST' });
        router.push(`/repos/${data.id}/scan`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(message);
      console.error('Error connecting repo:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* ── Connect form ─────────────────────────────────────── */}
      <div className="bg-white p-8 rounded-lg shadow">
        <h1 className="text-2xl font-bold mb-2">Connect a Repository</h1>
        <p className="text-gray-600 mb-6">
          Enter the URL of your Git repository to start generating AI documentation.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label htmlFor="repo-url" className="block text-sm font-medium text-gray-700 mb-1">
              Repository URL
            </label>
            <input
              id="repo-url"
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
              className="w-full border p-2 rounded focus:ring focus:ring-blue-200 focus:border-blue-500"
            />
          </div>

          {error && (
            <div role="alert" className="bg-red-50 text-red-700 border border-red-200 rounded p-3 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {loading ? 'Connecting...' : 'Connect and Scan'}
          </button>
        </form>
      </div>

      {/* ── Repo list ─────────────────────────────────────────── */}
      <div>
        <h2 className="text-lg font-semibold mb-4 text-gray-800">Your Repositories</h2>

        {fetchingRepos && (
          <p className="text-gray-400 text-sm">Loading repositories...</p>
        )}

        {!fetchingRepos && repos.length === 0 && (
          <div className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center text-gray-400">
            <p className="font-medium">No repositories connected yet.</p>
            <p className="text-sm mt-1">Connect your first repo above to get started.</p>
          </div>
        )}

        {repos.length > 0 && (
          <ul className="space-y-3">
            {repos.map((repo) => (
              <li
                key={repo.id}
                className="bg-white border rounded-lg p-4 flex items-center justify-between hover:shadow transition"
              >
                <div>
                  <p className="font-semibold text-gray-900">{repo.name}</p>
                  <p className="text-sm text-gray-500 truncate max-w-xs">{repo.url}</p>
                </div>
                <button
                  onClick={() => router.push(`/repos/${repo.id}/scan`)}
                  className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded transition"
                >
                  View Scan →
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
