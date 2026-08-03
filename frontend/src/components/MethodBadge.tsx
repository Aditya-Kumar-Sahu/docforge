import React from 'react';

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

interface MethodBadgeProps {
  method: HttpMethod | string;
  className?: string;
}

const methodColors: Record<string, string> = {
  GET: 'bg-green-100 text-green-800 border-green-200',
  POST: 'bg-blue-100 text-blue-800 border-blue-200',
  PUT: 'bg-amber-100 text-amber-800 border-amber-200',
  DELETE: 'bg-red-100 text-red-800 border-red-200',
  PATCH: 'bg-purple-100 text-purple-800 border-purple-200',
};

export function MethodBadge({ method, className = '' }: MethodBadgeProps) {
  const normalizedMethod = method.toUpperCase();
  const colorClass = methodColors[normalizedMethod] || 'bg-gray-100 text-gray-800 border-gray-200';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colorClass} ${className}`}>
      {normalizedMethod}
    </span>
  );
}
