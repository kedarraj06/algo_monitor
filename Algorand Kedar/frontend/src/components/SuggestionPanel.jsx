import React from 'react';

const SuggestionPanel = ({ suggestions = [], score = null }) => {
  // Score determination badge
  const renderScoreBadge = () => {
    if (score === null) return null;
    let color = '#34d399'; // green for 90+
    if (score < 50) color = '#f87171'; // red for <50
    else if (score < 90) color = '#fbbf24'; // yellow for 50-89

    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '12px' }}>
        <div style={{ position: 'relative', width: '60px', height: '60px', borderRadius: '50%', background: `conic-gradient(${color} ${score}%, transparent 0)` }}>
          <div style={{ position: 'absolute', inset: '4px', background: 'var(--surface-color)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '1.2rem', color: '#fff' }}>
            {score}
          </div>
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#fff' }}>Security Score</h3>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>0-100 Aggregate Rating</p>
        </div>
      </div>
    );
  };

  if (!suggestions || suggestions.length === 0) {
    return (
      <div className="glass-card result-container" style={{ marginTop: '2rem' }}>
        {renderScoreBadge()}
        <h2 style={{ marginBottom: '1rem', color: '#fff', fontSize: '1.4rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
          💡 Suggestions
        </h2>
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <span style={{ fontSize: '48px', display: 'block', marginBottom: '1rem' }}>🛡️</span>
          <h3 style={{ color: 'var(--safe-color)', fontSize: '1.4rem' }}>No Vulnerabilities Detected</h3>
          <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            The contract implements all essential security checks and patterns evaluated by our system.
          </p>
        </div>
      </div>
    );
  }

  const getSeverityBadge = (severity) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
      case 'HIGH':
        return <span className="severity-badge severity-high">🔴 {severity}</span>;
      case 'MEDIUM':
        return <span className="severity-badge severity-medium">🟡 {severity}</span>;
      case 'LOW':
        return <span className="severity-badge severity-low">🔵 {severity}</span>;
      default:
        return <span className="severity-badge">⚪ {severity}</span>;
    }
  };

  return (
    <div className="glass-card result-container" style={{ marginTop: '2rem' }}>
      {renderScoreBadge()}
      <h2 style={{ marginBottom: '2rem', color: '#fff', fontSize: '1.4rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        💡 Suggestions & Fixes
      </h2>

      <div className="suggestions-list" style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {suggestions.map((sug, idx) => (
          <div key={idx} className="suggestion-card" style={{ animationDelay: `${idx * 0.15}s` }}>
            <div className="suggestion-header">
              <h3 className="suggestion-title">{sug.issue}</h3>
              {getSeverityBadge(sug.severity || 'MEDIUM')}
            </div>

            <div className="suggestion-source">
              <span>Source: {sug.source}</span>
            </div>

            {sug.lines && sug.lines.length > 0 && (
              <div style={{ marginBottom: '1rem', fontSize: '0.85rem', color: '#fbbf24' }}>
                <strong>📍 Detected near line(s):</strong> {sug.lines.join(', ')}
              </div>
            )}

            <div className="suggestion-body">
              <h4 className="section-subtitle">Explanation</h4>
              <p className="suggestion-explanation" style={{ whiteSpace: 'pre-wrap' }}>{sug.explanation}</p>
            </div>

            {sug.fix && (
              <div className="suggestion-fix">
                <h4 className="section-subtitle">Recommended Fix</h4>
                <div className="code-block">
                  <pre>
                    <code>{sug.fix}</code>
                  </pre>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SuggestionPanel;
