'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { MethodBadge } from '../../../../components/MethodBadge';
import { QualityBadge } from '../../../../components/QualityBadge';
import { EndpointReviewCard, EndpointDetails } from '../../../../components/EndpointReviewCard';

type Status = 'pending' | 'approved' | 'rejected';

interface EndpointRow extends EndpointDetails {
  method: string;
  path: string;
  status: Status;
  qualityScore: number;
  qualityDimensions: { accuracy: number; completeness: number; clarity: number; examples: number; tone: number };
}

const FALLBACK_ENDPOINTS: EndpointRow[] = [
  {
    id: '1',
    title: 'Get User Profile',
    description: 'Retrieves the user profile for the authenticated user.',
    parameters: [
      { name: 'userId', type: 'string', required: true, description: 'The ID of the user' }
    ],
    responses: [
      { status: 200, description: 'User profile retrieved successfully' },
      { status: 404, description: 'User not found' }
    ],
    codeExamples: [
      { language: 'JavaScript', code: 'fetch("/api/users/123").then(res => res.json());' }
    ],
    sourceCode: 'export const getUser = async (req, res) => {\n  // Implementation\n};',
    method: 'GET',
    path: '/api/users/:userId',
    status: 'pending',
    qualityScore: 8.5,
    qualityDimensions: { accuracy: 8, completeness: 9, clarity: 8, examples: 9, tone: 8.5 }
  },
  {
    id: '2',
    title: 'Create Post',
    description: 'Creates a new blog post.',
    parameters: [],
    requestBody: '{\n  "title": "My Post",\n  "content": "Hello World"\n}',
    responses: [
      { status: 201, description: 'Post created' }
    ],
    codeExamples: [],
    sourceCode: 'export const createPost = async (req, res) => {\n  // Implementation\n};',
    method: 'POST',
    path: '/api/posts',
    status: 'pending',
    qualityScore: 6.2,
    qualityDimensions: { accuracy: 6, completeness: 7, clarity: 6, examples: 6, tone: 6 }
  }
];

export default function EndpointListPage() {
  const { id } = useParams();
  const repoId = typeof id === 'string' ? id : '';

  const [endpoints, setEndpoints] = useState<EndpointRow[]>(FALLBACK_ENDPOINTS);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | Status>('all');
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const [reviewEndpoint, setReviewEndpoint] = useState<EndpointRow | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchEndpoints = useCallback(async () => {
    if (!repoId) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/repos/${repoId}/endpoints`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          const mapped: EndpointRow[] = data.map((ep: Record<string, unknown>) => {
            const doc = (ep.generated_doc_json as Record<string, unknown>) || {};
            const qDims = (ep.quality_dimensions as { accuracy?: number; completeness?: number; clarity?: number; examples?: number; tone?: number }) || {};
            return {
              id: String(ep.id),
              method: String(ep.method || 'GET'),
              path: String(ep.path || ''),
              status: (ep.status === 'approved' || ep.status === 'rejected') ? ep.status : 'pending',
              qualityScore: typeof ep.quality_score === 'number' ? ep.quality_score : 7.0,
              qualityDimensions: {
                accuracy: qDims.accuracy ?? 7,
                completeness: qDims.completeness ?? 7,
                clarity: qDims.clarity ?? 7,
                examples: qDims.examples ?? 7,
                tone: qDims.tone ?? 7,
              },
              title: String(doc.title || `${ep.method} ${ep.path}`),
              description: String(doc.description || ''),
              parameters: (doc.parameters as unknown as Array<{ name: string; type: string; required: boolean; description: string }>) || [],
              requestBody: doc.request_body ? JSON.stringify(doc.request_body, null, 2) : undefined,
              responses: (doc.responses as unknown as Array<{ status: number; description: string }>) || [],
              codeExamples: doc.code_examples ? Object.entries(doc.code_examples as Record<string, unknown>).map(([lang, code]) => ({ language: lang, code: String(code) })) : [],
              sourceCode: String(ep.source_code_snippet || '')
            };
          });
          setEndpoints(mapped);
        }
      }
    } catch {
      // Retain fallback endpoints if offline or API error
    } finally {
      setLoading(false);
    }
  }, [repoId]);

  useEffect(() => {
    fetchEndpoints();
  }, [fetchEndpoints]);

  const filteredEndpoints = endpoints.filter(ep => {
    const matchesSearch = ep.path.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || ep.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleApprove = useCallback(async (epId: string) => {
    setEndpoints(prev => prev.map(ep => ep.id === epId ? { ...ep, status: 'approved' } : ep));
    setReviewEndpoint(null);
    try {
      await fetch(`/api/endpoints/${epId}/approve`, { method: 'PATCH' });
    } catch {
      // Optimistic update retained
    }
  }, []);

  const handleEditAndApprove = useCallback(async (editedEndpoint: EndpointDetails) => {
    setEndpoints(prev => prev.map(ep => ep.id === editedEndpoint.id ? { ...ep, ...editedEndpoint, status: 'approved' } : ep));
    setReviewEndpoint(null);
    try {
      await fetch(`/api/endpoints/${editedEndpoint.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: editedEndpoint.title,
          description: editedEndpoint.description,
          parameters: editedEndpoint.parameters,
        })
      });
      await fetch(`/api/endpoints/${editedEndpoint.id}/approve`, { method: 'PATCH' });
    } catch {
      // Optimistic update retained
    }
  }, []);

  const handleReject = useCallback(async (epId: string) => {
    setEndpoints(prev => prev.map(ep => ep.id === epId ? { ...ep, status: 'rejected' } : ep));
    setReviewEndpoint(null);
    try {
      await fetch(`/api/endpoints/${epId}/reject`, { method: 'PATCH' });
    } catch {
      // Optimistic update retained
    }
  }, []);

  const handleBulkApprove = async () => {
    setEndpoints(prev => prev.map(ep => (ep.status === 'pending' && ep.qualityScore > 7.0) ? { ...ep, status: 'approved' } : ep));
    if (repoId) {
      try {
        await fetch(`/api/repos/${repoId}/endpoints/bulk-approve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ min_quality_score: 7.0 })
        });
      } catch {
        // Optimistic update retained
      }
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (reviewEndpoint) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      switch (e.key) {
        case 'j':
          setSelectedIndex(prev => (prev < filteredEndpoints.length - 1 ? prev + 1 : prev));
          break;
        case 'k':
          setSelectedIndex(prev => (prev > 0 ? prev - 1 : prev));
          break;
        case 'a':
          if (selectedIndex >= 0 && selectedIndex < filteredEndpoints.length) {
            handleApprove(filteredEndpoints[selectedIndex].id);
          }
          break;
        case 'e':
          if (selectedIndex >= 0 && selectedIndex < filteredEndpoints.length) {
            setReviewEndpoint(filteredEndpoints[selectedIndex]);
          }
          break;
        case 'r':
          if (selectedIndex >= 0 && selectedIndex < filteredEndpoints.length) {
            handleReject(filteredEndpoints[selectedIndex].id);
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [filteredEndpoints, selectedIndex, handleApprove, handleReject, reviewEndpoint]);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Endpoints Review</h1>
        <button
          onClick={handleBulkApprove}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm font-medium"
        >
          Bulk Approve (&gt;7.0)
        </button>
      </div>

      <div className="flex gap-4 mb-6">
        <input
          type="text"
          placeholder="Search by path..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-2 flex-1 focus:ring-blue-500 focus:border-blue-500"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as 'all' | Status)}
          className="border border-gray-300 rounded-md px-3 py-2 bg-white focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-6 text-center text-gray-500">Loading endpoints...</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Method</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Path</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quality Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEndpoints.map((ep, idx) => (
                <tr
                  key={ep.id}
                  onClick={() => setReviewEndpoint(ep)}
                  className={`cursor-pointer hover:bg-gray-50 ${idx === selectedIndex ? 'bg-blue-50 ring-2 ring-inset ring-blue-500' : ''}`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <MethodBadge method={ep.method} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                    {ep.path}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <QualityBadge score={ep.qualityScore} dimensions={ep.qualityDimensions} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                      ${ep.status === 'approved' ? 'bg-green-100 text-green-800' :
                        ep.status === 'rejected' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {ep.status.charAt(0).toUpperCase() + ep.status.slice(1)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loading && filteredEndpoints.length === 0 && (
          <div className="p-6 text-center text-gray-500">No endpoints found.</div>
        )}
      </div>

      <div className="mt-6 text-sm text-gray-500 flex gap-4">
        <span><kbd className="bg-gray-100 border border-gray-300 rounded px-1">j</kbd> / <kbd className="bg-gray-100 border border-gray-300 rounded px-1">k</kbd> to navigate</span>
        <span><kbd className="bg-gray-100 border border-gray-300 rounded px-1">a</kbd> to approve</span>
        <span><kbd className="bg-gray-100 border border-gray-300 rounded px-1">r</kbd> to reject</span>
        <span><kbd className="bg-gray-100 border border-gray-300 rounded px-1">e</kbd> to edit</span>
      </div>

      {reviewEndpoint && (
        <EndpointReviewCard
          isOpen={true}
          onClose={() => setReviewEndpoint(null)}
          endpoint={reviewEndpoint}
          onApprove={() => handleApprove(reviewEndpoint.id)}
          onEditAndApprove={handleEditAndApprove}
          onReject={() => handleReject(reviewEndpoint.id)}
        />
      )}
    </div>
  );
}
