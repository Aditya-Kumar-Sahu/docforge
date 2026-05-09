"use client";

import { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Login with", email, password);
    // Placeholder for Supabase Auth
  };

  return (
    <div className="max-w-md mx-auto mt-12 bg-white p-8 border rounded-lg shadow-sm">
      <h1 className="text-2xl font-bold mb-6 text-center">Sign In to DocForge</h1>
      <form onSubmit={handleLogin} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input
            type="email"
            required
            className="mt-1 block w-full border rounded-md px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Password</label>
          <input
            type="password"
            required
            className="mt-1 block w-full border rounded-md px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded-md font-medium hover:bg-blue-700"
        >
          Sign In
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-gray-600">
        Don't have an account? <button className="text-blue-600 hover:underline">Sign Up</button>
      </p>
    </div>
  );
}
