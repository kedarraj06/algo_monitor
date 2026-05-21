import React from 'react';

interface Suggestion {
  line?: number;
  vulnerability: string;
  description: string;
  fix: string;
  severity: string;
}

interface SuggestionPanelProps {
  suggestions: Suggestion[];
  score: number;
  summary: string;
}

export const SuggestionPanel: React.FC<SuggestionPanelProps> = ({ suggestions, score, summary }) => {
  const getSeverityBorder = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL': return 'border-l-danger';
      case 'HIGH': return 'border-l-orange-500';
      case 'MEDIUM': return 'border-l-warning';
      case 'LOW': return 'border-l-blue-500';
      default: return 'border-l-gray-500';
    }
  };

  const scoreColor = score >= 70 ? 'text-safe' : score >= 40 ? 'text-warning' : 'text-danger';

  if (!suggestions || suggestions.length === 0) {
    return (
      <div className="mt-6 p-6 bg-white/5 border border-white/10 rounded-lg text-center">
        <span className="text-4xl block mb-4">🛡️</span>
        <h3 className="text-safe text-xl font-bold mb-2">No Vulnerabilities Detected</h3>
        <p className="text-gray-400">The contract implements all essential security checks and patterns evaluated by our AI.</p>
      </div>
    );
  }

  return (
    <div className="mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-3 font-syne font-bold flex items-center gap-2">
        <span className="text-lg">🧠</span> AI Fix Suggestions
      </h3>
      
      <div className="flex items-center gap-4 mb-4 p-3 bg-white/5 rounded-lg border border-white/10">
        <span className="text-gray-400 text-sm font-mono">AI Security Score:</span>
        <span className={`font-mono font-bold text-lg ${scoreColor}`}>
          {score}/100
        </span>
        <span className="text-gray-500 text-sm ml-auto hidden sm:block">{summary}</span>
      </div>
      
      <div className="space-y-4">
        {suggestions.map((s, i) => (
          <div key={i} className={`bg-white/5 border border-white/10 border-l-4 rounded-lg p-4 ${getSeverityBorder(s.severity)}`}>
            <div className="flex gap-3 items-center mb-2">
              <span className="bg-white/10 rounded px-2 py-1 text-xs text-gray-400 font-mono">
                Line {s.line || 'N/A'}
              </span>
              <span className="font-semibold text-gray-200 text-sm">{s.vulnerability}</span>
            </div>
            <p className="text-gray-400 text-sm mb-4">{s.description}</p>
            <div className="bg-safe/5 border border-safe/20 rounded-md p-3 relative">
              <span className="absolute -top-3 right-4 bg-background px-2 text-xs text-safe font-mono border border-safe/20 rounded">RECOMMENDED FIX</span>
              <pre className="text-safe text-sm font-mono whitespace-pre-wrap mt-2 overflow-x-auto">
                <code>{s.fix}</code>
              </pre>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
