'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function RepoConnectorPage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch('/api/repos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      
      const data = await res.json();
      
      if (data.id) {
        await fetch(`/api/repos/${data.id}/scan`, { method: 'POST' });
        router.push(`/repos/${data.id}/scan`);
      }
    } catch (error) {
      console.error('Error connecting repo:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto bg-white p-8 rounded shadow">
      <h1 className="text-2xl font-bold mb-4">Connect a Repository</h1>
      <p className="text-gray-600 mb-6">Enter the URL of your Git repository to start generating AI documentation.</p>
      
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
        <button 
          type="submit" 
          disabled={loading}
          className="bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {loading ? 'Connecting...' : 'Connect and Scan'}
        </button>
      </form>
    </div>
  );
}
