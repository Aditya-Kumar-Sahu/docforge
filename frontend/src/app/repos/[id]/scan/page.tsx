'use client';

import { useSSE } from '@/hooks/useSSE';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

interface ScanProgress {
  status: string;
  progress: number;
}

export default function ScanProgressPage() {
  const params = useParams();
  const id = params.id as string;
  
  const { data, isConnected, error } = useSSE<ScanProgress>(`/api/repos/${id}/scan-stream`);
  const [fallbackData, setFallbackData] = useState<ScanProgress | null>(null);

  useEffect(() => {
    if (!isConnected && !data) {
      fetch(`/api/repos/${id}/scan-progress`)
        .then(res => res.json())
        .then(resData => setFallbackData(resData))
        .catch(err => console.error("Polling error", err));
    }
  }, [id, isConnected, data]);

  const currentData = data || fallbackData;

  return (
    <div className="max-w-xl mx-auto bg-white p-8 rounded shadow text-center">
      <h1 className="text-2xl font-bold mb-4">Scanning Repository</h1>
      <p className="text-gray-600 mb-8">Please wait while DocForge analyzes your codebase...</p>
      
      {error && !fallbackData && (
        <div className="bg-red-50 text-red-600 p-4 rounded mb-4">
          Error connecting to live scan updates.
        </div>
      )}

      <div className="w-full bg-gray-200 rounded-full h-4 mb-4 overflow-hidden">
        <div 
          className="bg-blue-600 h-4 rounded-full transition-all duration-500 ease-in-out" 
          style={{ width: `${currentData?.progress || 0}%` }}
        ></div>
      </div>
      
      <div className="text-sm font-medium text-gray-500 capitalize">
        Status: {currentData?.status || 'Initializing...'}
      </div>
    </div>
  );
}
