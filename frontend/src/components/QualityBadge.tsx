import React, { useState } from 'react';

export interface QualityDimensions {
  accuracy: number;
  completeness: number;
  clarity: number;
  examples: number;
  tone: number;
}

interface QualityBadgeProps {
  score: number;
  dimensions?: QualityDimensions;
  className?: string;
}

export function QualityBadge({ score, dimensions, className = '' }: QualityBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  let colorClass = 'bg-red-100 text-red-800 border-red-200';
  if (score >= 7) {
    colorClass = 'bg-green-100 text-green-800 border-green-200';
  } else if (score >= 5) {
    colorClass = 'bg-amber-100 text-amber-800 border-amber-200';
  }

  return (
    <div 
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colorClass} cursor-help`}>
        Score: {score.toFixed(1)}
      </span>
      
      {showTooltip && dimensions && (
        <div className="absolute z-10 bottom-full mb-2 left-1/2 -translate-x-1/2 w-48 bg-white border border-gray-200 rounded-md shadow-lg p-3 text-xs text-gray-700">
          <div className="font-semibold mb-2 text-gray-900 border-b pb-1">Quality Breakdown</div>
          <div className="flex justify-between py-0.5">
            <span>Accuracy:</span>
            <span className="font-medium">{dimensions.accuracy.toFixed(1)}</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span>Completeness:</span>
            <span className="font-medium">{dimensions.completeness.toFixed(1)}</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span>Clarity:</span>
            <span className="font-medium">{dimensions.clarity.toFixed(1)}</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span>Examples:</span>
            <span className="font-medium">{dimensions.examples.toFixed(1)}</span>
          </div>
          <div className="flex justify-between py-0.5">
            <span>Tone:</span>
            <span className="font-medium">{dimensions.tone.toFixed(1)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
