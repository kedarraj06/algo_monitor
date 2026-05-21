import React from 'react';

interface CodeViewerProps {
  code: string;
  highlights: number[];
}

export const CodeViewer = ({ code, highlights }: CodeViewerProps) => {
  const lines = code.split('\n');

  return (
    <div className="rounded-xl overflow-hidden border border-border bg-[#050505] shadow-inner relative max-h-[600px] overflow-y-auto">
      <div className="sticky top-0 bg-surface border-b border-border px-4 py-2 flex justify-between items-center z-10 backdrop-blur-md">
        <span className="text-xs font-mono text-gray-400">contract.teal</span>
      </div>
      <pre className="p-4 text-sm font-mono text-gray-300 leading-relaxed">
        <code>
          {lines.map((line, i) => {
            const lineNum = i + 1;
            const highlighted = highlights.includes(lineNum);
            
            return (
              <div 
                key={lineNum} 
                className={`flex gap-4 px-2 -mx-2 rounded ${
                  highlighted ? 'bg-danger/20 border-l-2 border-danger' : 'hover:bg-surface-hover border-l-2 border-transparent'
                }`}
              >
                <span className="text-gray-600 select-none w-8 text-right shrink-0">{lineNum}</span>
                <span className={highlighted ? 'text-danger font-bold' : ''}>{line}</span>
              </div>
            );
          })}
        </code>
      </pre>
    </div>
  );
};
