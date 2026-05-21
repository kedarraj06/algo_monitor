import React, { useState } from 'react';

const UploadCard = ({ 
  file, 
  contractHash, 
  email,
  dragActive, 
  loading, 
  error, 
  handleDrag, 
  handleDrop, 
  handleChange, 
  handleHashChange,
  handleEmailChange,
  handleAnalyzeRisk,
  handleGetSuggestions,
  handleStartMonitoring,
  activeView
}) => {
  const [validationError, setValidationError] = useState('');

  const onAnalyzeClick = () => {
    if (!file) {
      setValidationError('Please upload a .teal file first.');
      return;
    }
    setValidationError('');
    handleAnalyzeRisk();
  };

  const onSuggestClick = () => {
    if (!file) {
      setValidationError('Please upload a .teal file first.');
      return;
    }
    setValidationError('');
    handleGetSuggestions();
  };

  const onMonitorClick = () => {
    if (!contractHash.trim()) {
      setValidationError('Please enter a contract address or hash.');
      return;
    }
    if (!email.trim() || !email.includes('@')) {
      setValidationError('Please enter a valid email address.');
      return;
    }
    setValidationError('');
    handleStartMonitoring();
  };

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
      
      {/* Analysis Section */}
      <div className="section-container">
        <div className="section-header" style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
          <h2 className="section-title" style={{ fontSize: '1.4rem', color: '#fff', margin: 0, fontWeight: '600' }}>Static Analysis</h2>
          <p className="section-subtitle" style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '0.2rem 0 0 0' }}>Upload a .teal file to evaluate</p>
        </div>

        <div 
          className={`file-upload-area ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-upload').click()}
          style={{ marginBottom: '1.5rem' }}
        >
          <input 
            type="file" 
            id="file-upload" 
            accept=".teal" 
            style={{ display: 'none' }} 
            onChange={(e) => { setValidationError(''); handleChange(e); }}
          />
          <div className="upload-icon" style={{ fontSize: '48px' }}>📁</div>
          
          {file ? (
            <div style={{ animation: 'slideUp 0.3s ease' }}>
              <h3 style={{ color: '#60a5fa', fontSize: '1.4rem', marginBottom: '0.5rem' }}>{file.name}</h3>
              <p style={{ color: 'var(--text-muted)' }}>Click or drag a different file to replace</p>
            </div>
          ) : (
            <div>
              <h3 style={{ fontSize: '1.4rem', marginBottom: '0.5rem' }}>Upload your TEAL file</h3>
              <p style={{ color: 'var(--text-muted)' }}>Drag and drop or click to browse</p>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button 
            className={`btn btn-action ${activeView === 'risk' ? 'active-btn' : ''}`} 
            onClick={onAnalyzeClick} 
            disabled={loading}
            style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', background: activeView === 'risk' ? 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)' : 'rgba(255,255,255,0.05)', border: activeView === 'risk' ? '1px solid #3b82f6' : '1px solid var(--glass-border)' }}
          >
            {loading && activeView === 'risk' ? (
              <><div className="loading-spinner small"></div> Analyzing...</>
            ) : (
              <>🔍 Analyze Risk</>
            )}
          </button>
          
          <button 
            className={`btn btn-action ${activeView === 'suggestions' ? 'active-btn' : ''}`} 
            onClick={onSuggestClick} 
            disabled={loading}
            style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', background: activeView === 'suggestions' ? 'linear-gradient(135deg, #059669 0%, #047857 100%)' : 'rgba(255,255,255,0.05)', border: activeView === 'suggestions' ? '1px solid #10b981' : '1px solid var(--glass-border)' }}
          >
            {loading && activeView === 'suggestions' ? (
              <><div className="loading-spinner small"></div> Fetching...</>
            ) : (
              <>💡 Get Suggestions</>
            )}
          </button>
        </div>
      </div>

      <div className="divider" style={{ height: '1px', background: 'var(--glass-border)', width: '100%', margin: '0' }}></div>

      {/* Monitoring Section */}
      <div className="section-container">
        <div className="section-header" style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
          <h2 className="section-title" style={{ fontSize: '1.4rem', color: '#fff', margin: 0, fontWeight: '600' }}>Continuous Monitoring</h2>
          <p className="section-subtitle" style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '0.2rem 0 0 0' }}>Real-time threat detection</p>
        </div>
        
        <div className="input-group" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', textAlign: 'left' }}>
          <label className="input-label" style={{ color: '#cbd5e1', fontSize: '0.9rem', fontWeight: '500' }}>Contract Address / Hash</label>
          <input 
            type="text" 
            placeholder="e.g., ABC123DEF456..." 
            value={contractHash}
            onChange={(e) => { setValidationError(''); handleHashChange(e); }}
            className="modern-input"
            style={{
              padding: '1rem',
              borderRadius: '12px',
              background: 'rgba(0, 0, 0, 0.2)',
              border: '1px solid var(--glass-border)',
              color: '#fff',
              fontSize: '1rem',
              width: '100%',
              boxSizing: 'border-box',
              transition: 'all 0.2s ease',
              outline: 'none'
            }}
            onFocus={(e) => e.target.style.borderColor = '#8b5cf6'}
            onBlur={(e) => e.target.style.borderColor = 'var(--glass-border)'}
          />
        </div>

        <div className="input-group" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', textAlign: 'left', marginTop: '1rem' }}>
          <label className="input-label" style={{ color: '#cbd5e1', fontSize: '0.9rem', fontWeight: '500' }}>Alert Email Address</label>
          <input 
            type="email" 
            placeholder="your@email.com" 
            value={email}
            onChange={(e) => { setValidationError(''); handleEmailChange(e); }}
            className="modern-input"
            style={{
              padding: '1rem',
              borderRadius: '12px',
              background: 'rgba(0, 0, 0, 0.2)',
              border: '1px solid var(--glass-border)',
              color: '#fff',
              fontSize: '1rem',
              width: '100%',
              boxSizing: 'border-box',
              transition: 'all 0.2s ease',
              outline: 'none'
            }}
            onFocus={(e) => e.target.style.borderColor = '#8b5cf6'}
            onBlur={(e) => e.target.style.borderColor = 'var(--glass-border)'}
          />
        </div>
        
        <button 
          className={`btn btn-monitor ${activeView === 'monitoring' ? 'active-btn' : ''}`} 
          onClick={onMonitorClick} 
          disabled={loading}
          style={{ width: '100%', marginTop: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', background: activeView === 'monitoring' ? 'linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%)' : 'rgba(255,255,255,0.05)', border: activeView === 'monitoring' ? '1px solid #8b5cf6' : '1px solid var(--glass-border)' }}
        >
          {loading && activeView === 'monitoring' ? (
            <><div className="loading-spinner small"></div> Starting...</>
          ) : (
            <>📡 Start Monitoring</>
          )}
        </button>
      </div>

      {(error || validationError) && (
        <div className="error-message" style={{ marginTop: '0.5rem', padding: '1rem', borderRadius: '8px', background: 'rgba(239,68,68,0.1)', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.3)', textAlign: 'center' }}>
          {error || validationError}
        </div>
      )}

    </div>
  );
};

export default UploadCard;
