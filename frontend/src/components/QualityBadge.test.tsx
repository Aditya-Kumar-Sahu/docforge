import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QualityBadge } from './QualityBadge';
import React from 'react';

describe('QualityBadge', () => {
  it('renders correctly with score >= 7 (green)', () => {
    render(<QualityBadge score={8.5} />);
    const badge = screen.getByText('Score: 8.5');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-green-100');
  });

  it('renders correctly with score 5-7 (amber)', () => {
    render(<QualityBadge score={6.5} />);
    const badge = screen.getByText('Score: 6.5');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-amber-100');
  });

  it('renders correctly with score < 5 (red)', () => {
    render(<QualityBadge score={4.5} />);
    const badge = screen.getByText('Score: 4.5');
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('bg-red-100');
  });

  it('shows tooltip on hover when dimensions are provided', async () => {
    const dimensions = { accuracy: 8, completeness: 9, clarity: 7, examples: 8, tone: 9 };
    render(<QualityBadge score={8.2} dimensions={dimensions} />);
    
    const badgeContainer = screen.getByText('Score: 8.2').parentElement;
    if (badgeContainer) {
      fireEvent.mouseEnter(badgeContainer);
      expect(await screen.findByText('Quality Breakdown')).toBeInTheDocument();
      expect(screen.getByText('Accuracy:')).toBeInTheDocument();
      expect(screen.getAllByText('8.0')[0]).toBeInTheDocument();
    }
  });
});
