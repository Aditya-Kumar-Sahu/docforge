import React, { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export interface EndpointDetails {
  id: string;
  title: string;
  description: string;
  parameters: Array<{ name: string; type: string; required: boolean; description: string }>;
  requestBody?: string;
  responses: Array<{ status: number; description: string }>;
  codeExamples: Array<{ language: string; code: string }>;
  sourceCode: string;
}

interface EndpointReviewCardProps {
  isOpen: boolean;
  onClose: () => void;
  endpoint: EndpointDetails;
  onApprove: () => void;
  onEditAndApprove: (editedEndpoint: EndpointDetails) => void;
  onReject: () => void;
}

export function EndpointReviewCard({ isOpen, onClose, endpoint, onApprove, onEditAndApprove, onReject }: EndpointReviewCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedDescription, setEditedDescription] = useState(endpoint.description);

  const handleApprove = () => {
    if (isEditing) {
      onEditAndApprove({ ...endpoint, description: editedDescription });
    } else {
      onApprove();
    }
  };

  return (
    <Transition.Root show={isOpen} as={React.Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <div className="fixed inset-0 bg-gray-900/50 transition-opacity" />

        <div className="fixed inset-0 overflow-hidden">
          <div className="absolute inset-0 overflow-hidden">
            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10 sm:pl-16">
              <Transition.Child
                as={React.Fragment}
                enter="transform transition ease-in-out duration-300 sm:duration-500"
                enterFrom="translate-x-full"
                enterTo="translate-x-0"
                leave="transform transition ease-in-out duration-300 sm:duration-500"
                leaveFrom="translate-x-0"
                leaveTo="translate-x-full"
              >
                <Dialog.Panel className="pointer-events-auto w-screen max-w-6xl">
                  <div className="flex h-full flex-col divide-y divide-gray-200 bg-white shadow-xl">
                    <div className="flex min-h-0 flex-1 overflow-y-auto">
                      {/* Left Panel: Doc Preview */}
                      <div className="flex-1 p-6 overflow-y-auto border-r border-gray-200">
                        <Dialog.Title className="text-2xl font-semibold text-gray-900 mb-4">
                          {endpoint.title}
                        </Dialog.Title>
                        
                        <div className="mb-6">
                          <h3 className="text-lg font-medium text-gray-900 mb-2">Description</h3>
                          {isEditing ? (
                            <textarea
                              className="w-full h-32 p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                              value={editedDescription}
                              onChange={(e) => setEditedDescription(e.target.value)}
                            />
                          ) : (
                            <p className="text-gray-700">{endpoint.description}</p>
                          )}
                        </div>

                        {endpoint.parameters.length > 0 && (
                          <div className="mb-6">
                            <h3 className="text-lg font-medium text-gray-900 mb-2">Parameters</h3>
                            <ul className="space-y-2">
                              {endpoint.parameters.map((param, idx) => (
                                <li key={idx} className="bg-gray-50 p-3 rounded-md">
                                  <span className="font-semibold">{param.name}</span>
                                  <span className="text-gray-500 text-sm ml-2">({param.type})</span>
                                  {param.required && <span className="text-red-500 text-sm ml-2">*required</span>}
                                  <p className="text-gray-600 mt-1">{param.description}</p>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {endpoint.requestBody && (
                          <div className="mb-6">
                            <h3 className="text-lg font-medium text-gray-900 mb-2">Request Body</h3>
                            <pre className="bg-gray-100 p-3 rounded-md overflow-x-auto">
                              <code>{endpoint.requestBody}</code>
                            </pre>
                          </div>
                        )}

                        <div className="mb-6">
                          <h3 className="text-lg font-medium text-gray-900 mb-2">Responses</h3>
                          <ul className="space-y-2">
                            {endpoint.responses.map((resp, idx) => (
                              <li key={idx} className="flex gap-4 bg-gray-50 p-3 rounded-md">
                                <span className="font-semibold text-blue-600">{resp.status}</span>
                                <span className="text-gray-700">{resp.description}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        {endpoint.codeExamples.length > 0 && (
                          <div className="mb-6">
                            <h3 className="text-lg font-medium text-gray-900 mb-2">Examples</h3>
                            {endpoint.codeExamples.map((ex, idx) => (
                              <div key={idx} className="mb-4">
                                <h4 className="text-sm font-medium text-gray-500 mb-1">{ex.language}</h4>
                                <SyntaxHighlighter language={ex.language.toLowerCase()} style={vscDarkPlus} className="rounded-md text-sm">
                                  {ex.code}
                                </SyntaxHighlighter>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Right Panel: Source Code */}
                      <div className="w-1/2 flex flex-col bg-gray-900">
                        <div className="p-4 border-b border-gray-700">
                          <h3 className="text-lg font-medium text-gray-100">Source Code Snippet</h3>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4">
                          <SyntaxHighlighter 
                            language="typescript" 
                            style={vscDarkPlus} 
                            customStyle={{ margin: 0, background: 'transparent' }}
                            showLineNumbers
                          >
                            {endpoint.sourceCode}
                          </SyntaxHighlighter>
                        </div>
                      </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="flex flex-shrink-0 justify-between px-4 py-4">
                      <div className="flex gap-3">
                        <button
                          type="button"
                          className="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                          onClick={() => setIsEditing(!isEditing)}
                        >
                          {isEditing ? 'Cancel Edit' : 'Edit Description'}
                        </button>
                      </div>
                      <div className="flex gap-3">
                        <button
                          type="button"
                          className="rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500"
                          onClick={onReject}
                        >
                          Reject
                        </button>
                        <button
                          type="button"
                          className="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                          onClick={onClose}
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                          onClick={handleApprove}
                        >
                          {isEditing ? 'Save & Approve' : 'Approve'}
                        </button>
                      </div>
                    </div>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
}
