"use client";

import { useState } from "react";

interface Repo {
  id: number;
  full_name: string;
  status: "idle" | "scanning" | "completed";
}

export default function ReposPage() {
  const [repos, setRepos] = useState<Repo[]>([
    { id: 1, full_name: "docforge/backend", status: "completed" },
    { id: 2, full_name: "fastapi/fastapi", status: "idle" },
  ]);
  const [newRepo, setNewRepo] = useState("");

  const handleAddRepo = () => {
    if (!newRepo) return;
    const nextId = repos.length > 0 ? Math.max(...repos.map(r => r.id)) + 1 : 1;
    setRepos([...repos, { id: nextId, full_name: newRepo, status: "idle" }]);
    setNewRepo("");
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Your Repositories</h1>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="owner/repo"
            className="border rounded-md px-3 py-2 text-sm w-64"
            value={newRepo}
            onChange={(e) => setNewRepo(e.target.value)}
          />
          <button
            onClick={handleAddRepo}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
          >
            Connect
          </button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg divide-y">
        {repos.map((repo) => (
          <div key={repo.id} className="p-4 flex justify-between items-center">
            <div>
              <p className="font-medium text-gray-900">{repo.full_name}</p>
              <p className="text-sm text-gray-500 capitalize">{repo.status}</p>
            </div>
            <div className="flex gap-2">
              <button className="text-sm text-blue-600 hover:underline">View Docs</button>
              <button className="text-sm border px-3 py-1 rounded hover:bg-gray-50">
                Scan
              </button>
            </div>
          </div>
        ))}
        {repos.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            No repositories connected yet.
          </div>
        )}
      </div>
    </div>
  );
}
