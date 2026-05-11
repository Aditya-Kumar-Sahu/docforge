"use client";

import { useSSE } from "@/hooks/useSSE";
import { useParams, useRouter } from "next/navigation";

interface ScanEvent {
  status: string;
  repo_id: number;
}

export default function ScanProgressPage() {
  const params = useParams();
  const router = useRouter();
  const repoId = params.id as string;

  const { data, error } = useSSE<ScanEvent>(
    `http://localhost:8000/api/repos/${repoId}/scan-progress`
  );

  return (
    <div className="max-w-2xl mx-auto mt-12 text-center">
      <h1 className="text-2xl font-bold mb-4">Scanning Repository...</h1>
      
      <div className="bg-white p-8 rounded-lg shadow-sm border">
        <div className="flex flex-col items-center gap-6">
          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div 
              className={`h-full bg-blue-600 transition-all duration-500 ${
                data?.status === "completed" ? "w-full" : "w-1/2 animate-pulse"
              }`}
            ></div>
          </div>
          
          <div className="text-lg font-medium text-gray-700">
            {data?.status === "scanning" && "Analyzing code structure..."}
            {data?.status === "completed" && "Scan complete!"}
            {data?.status === "failed" && "Scan failed."}
            {!data && !error && "Connecting to scanner..."}
            {error && "Connection lost. Please retry."}
          </div>

          {data?.status === "completed" && (
            <button
              onClick={() => router.push("/repos")}
              className="bg-blue-600 text-white px-6 py-2 rounded-md font-medium hover:bg-blue-700"
            >
              Back to Repos
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
