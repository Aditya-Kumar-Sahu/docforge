import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MethodBadge } from './MethodBadge';
import React from 'react';

describe('MethodBadge', () => {
  it('renders correctly with GET method', () => {
    render(<MethodBadge method="GET" />);
    const badge = screen.getByText('GET');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-green-100');
  });

  it('renders correctly with POST method', () => {
    render(<MethodBadge method="POST" />);
    const badge = screen.getByText('POST');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-blue-100');
  });

  it('handles lowercase methods', () => {
    render(<MethodBadge method="delete" />);
    const badge = screen.getByText('DELETE');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-red-100');
  });

  it('applies fallback for unknown methods', () => {
    render(<MethodBadge method="UNKNOWN" />);
    const badge = screen.getByText('UNKNOWN');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-gray-100');
  });
});
