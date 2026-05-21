import React, { useEffect, useRef } from 'react';

interface CodeViewerProps {
  code: string;
  highlights: number[];
  focusedLine?: number | null;
  onLineClick?: (lineNum: number) => void;
}

export const CodeViewer = ({ code, highlights, focusedLine, onLineClick }: CodeViewerProps) => {
  const lines = code.split('\n');
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (focusedLine && containerRef.current) {
      const lineElement = containerRef.current.querySelector(`#teal-line-${focusedLine}`);
      if (lineElement) {
        lineElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        });
      }
    }
  }, [focusedLine]);

  return (
    <div 
      ref={containerRef}
      className="rounded-xl overflow-hidden border border-border bg-[#050505] shadow-inner relative max-h-[600px] overflow-y-auto"
    >
      <div className="sticky top-0 bg-surface border-b border-border px-4 py-2 flex justify-between items-center z-10 backdrop-blur-md">
        <span className="text-xs font-mono text-gray-400">contract.teal</span>
        {focusedLine && (
          <span className="text-xs font-mono text-primary animate-pulse">
            Focused on Line {focusedLine}
          </span>
        )}
      </div>
      <pre className="p-4 text-sm font-mono text-gray-300 leading-relaxed">
        <code>
          {lines.map((line, i) => {
            const lineNum = i + 1;
            const highlighted = highlights.includes(lineNum);
            const isFocused = focusedLine === lineNum;
            
            return (
              <div 
                key={lineNum} 
                id={`teal-line-${lineNum}`}
                onClick={() => onLineClick?.(lineNum)}
                className={`flex gap-4 px-2 -mx-2 rounded cursor-pointer transition-all duration-300 ${
                  isFocused 
                    ? 'bg-primary/15 border-l-2 border-primary shadow-[inset_0_0_8px_rgba(0,255,136,0.15)] font-bold text-primary'
                    : highlighted 
                      ? 'bg-danger/20 border-l-2 border-danger text-danger font-bold hover:bg-danger/30' 
                      : 'hover:bg-surface-hover border-l-2 border-transparent'
                }`}
              >
                <span className={`select-none w-8 text-right shrink-0 ${
                  isFocused ? 'text-primary' : highlighted ? 'text-danger' : 'text-gray-600'
                }`}>{lineNum}</span>
                <span className="break-all">{line}</span>
              </div>
            );
          })}
        </code>
      </pre>
    </div>
  );
};

