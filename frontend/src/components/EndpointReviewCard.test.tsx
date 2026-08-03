import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EndpointReviewCard, EndpointDetails } from './EndpointReviewCard';
import React from 'react';

const mockEndpoint: EndpointDetails = {
  id: '1',
  title: 'Test Endpoint',
  description: 'Test description',
  parameters: [],
  responses: [{ status: 200, description: 'OK' }],
  codeExamples: [],
  sourceCode: 'const test = true;'
};

describe('EndpointReviewCard', () => {
  it('renders endpoint details when open', () => {
    render(
      <EndpointReviewCard 
        isOpen={true} 
        onClose={vi.fn()} 
        endpoint={mockEndpoint} 
        onApprove={vi.fn()} 
        onEditAndApprove={vi.fn()} 
        onReject={vi.fn()} 
      />
    );
    expect(screen.getByText('Test Endpoint')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    // Note: Headless UI Dialog might still be in the DOM but hidden, depending on transition setup. 
    // Usually it removes from DOM or aria-hidden=true.
    render(
      <EndpointReviewCard 
        isOpen={false} 
        onClose={vi.fn()} 
        endpoint={mockEndpoint} 
        onApprove={vi.fn()} 
        onEditAndApprove={vi.fn()} 
        onReject={vi.fn()} 
      />
    );
    expect(screen.queryByText('Test Endpoint')).not.toBeInTheDocument();
  });
});
