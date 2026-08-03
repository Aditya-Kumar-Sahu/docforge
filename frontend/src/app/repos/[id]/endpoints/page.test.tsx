import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import EndpointListPage from './page';
import React from 'react';

// Mock useParams from next/navigation
vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'repo-123' })
}));

describe('EndpointListPage', () => {
  it('renders the page title and initial endpoints', async () => {
    render(<EndpointListPage />);
    expect(screen.getByText('Endpoints Review')).toBeInTheDocument();
    
    // Check for some mock data
    expect(await screen.findByText('/api/users/:userId')).toBeInTheDocument();
    expect(screen.getByText('/api/posts')).toBeInTheDocument();
  });
});
