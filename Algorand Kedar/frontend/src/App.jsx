import React, { useState } from 'react';
import './index.css';
import UploadCard from './components/UploadCard';
import SuggestionPanel from './components/SuggestionPanel';
import MonitoringPanel from './components/MonitoringPanel';

function App() {
  // Input states
  const [file, setFile] = useState(null);
  const [contractHash, setContractHash] = useState('');
  const [email, setEmail] = useState('');
  
  // UI states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  
  // Result states
  const [predictionResult, setPredictionResult] = useState(null);
  const [suggestionResult, setSuggestionResult] = useState(null);
  const [monitoringStatus, setMonitoringStatus] = useState({ isMonitoring: false, hash: null });
  
  // View state: 'risk', 'suggestions', 'monitoring', or null
  const [activeView, setActiveView] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave" || e.type === "drop") {
      setDragActive(false);
    }
  };

  const processFile = (selectedFile) => {
    if (selectedFile && selectedFile.name.endsWith('.teal')) {
      setFile(selectedFile);
      setError(null);
      // Reset views when new file is uploaded
      setActiveView(null);
      setPredictionResult(null);
      setSuggestionResult(null);
    } else {
      setError("Please upload a valid .teal smart contract file.");
      setFile(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleHashChange = (e) => {
    setContractHash(e.target.value);
    if (error) setError(null);
  };

  const handleEmailChange = (e) => {
    setEmail(e.target.value);
    if (error) setError(null);
  };

  // API Caller for Prediction
  const callAnalyzeAPI = async () => {
    const formData = new FormData();
    formData.append('file', file);

    const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    const response = await fetch(`${apiUrl}/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let errorMsg = 'Risk analysis failed. Please try again.';
      try {
        const errData = await response.json();
        errorMsg = errData.detail || errorMsg;
      } catch (e) {
        console.debug("Non-JSON error response", e);
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  };

  // API Caller for Suggestions
  const callSuggestAPI = async () => {
    const formData = new FormData();
    formData.append('file', file);

    const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    const response = await fetch(`${apiUrl}/suggest`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let errorMsg = 'Failed to fetch suggestions. Please try again.';
      try {
        const errData = await response.json();
        errorMsg = errData.detail || errorMsg;
      } catch (e) {
        console.debug("Non-JSON error response", e);
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  };

  const handleAnalyzeRisk = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setActiveView('risk');

    try {
      const data = await callAnalyzeAPI();
      // Ensure smooth visual transition
      setTimeout(() => {
        setPredictionResult({
          label: data.label,
          features: data.features
        });
        setLoading(false);
      }, 600);
    } catch (err) {
      setTimeout(() => {
        setError(err.message);
        setLoading(false);
      }, 600);
    }
  };

  const handleGetSuggestions = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setActiveView('suggestions');

    try {
      const data = await callSuggestAPI();
      setTimeout(() => {
        setSuggestionResult({
          suggestions: data.suggestions,
          score: data.score
        });
        setLoading(false);
      }, 600);
    } catch (err) {
      setTimeout(() => {
        setError(err.message);
        setLoading(false);
      }, 600);
    }
  };

  const handleStartMonitoring = async () => {
    if (!contractHash || !email) return;
    setLoading(true);
    setError(null);
    setActiveView('monitoring');

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${apiUrl}/monitor/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contract_address: contractHash,
          email: email
        }),
      });

      if (!response.ok) {
        let errorMsg = 'Failed to start monitoring. Please try again.';
        try {
          const errData = await response.json();
          errorMsg = errData.detail || errorMsg;
        } catch (e) {}
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setTimeout(() => {
        setMonitoringStatus({
          isMonitoring: true,
          hash: contractHash
        });
        setLoading(false);
      }, 600);
    } catch (err) {
      setTimeout(() => {
        setError(err.message);
        setLoading(false);
      }, 600);
    }
  };

  const formatFeatureName = (name) => {
    if (!name) return '';
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getStatusIcon = (label) => {
    if (label === 'SAFE') return <span style={{ marginRight: '16px', fontSize: '32px' }}>✅</span>;
    if (label === 'SUSPICIOUS') return <span style={{ marginRight: '16px', fontSize: '32px' }}>⚠️</span>;
    return <span style={{ marginRight: '16px', fontSize: '32px' }}>❌</span>;
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>AlgoShield AI</h1>
        <p>Intelligent Security Analysis for Algorand TEAL Smart Contracts</p>
      </header>

      <main>
        <UploadCard 
          file={file}
          contractHash={contractHash}
          email={email}
          dragActive={dragActive}
          loading={loading}
          error={error}
          handleDrag={handleDrag}
          handleDrop={handleDrop}
          handleChange={handleChange}
          handleHashChange={handleHashChange}
          handleEmailChange={handleEmailChange}
          handleAnalyzeRisk={handleAnalyzeRisk}
          handleGetSuggestions={handleGetSuggestions}
          handleStartMonitoring={handleStartMonitoring}
          activeView={activeView}
        />

        {/* View 1: Analyze Risk */}
        {activeView === 'risk' && predictionResult && (
          <div className="glass-card result-container" style={{ marginTop: '2rem', animation: 'fadeIn 0.5s ease' }}>
            <h2 style={{ marginBottom: '2rem', color: '#fff', fontSize: '1.4rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              🔍 Risk Analysis Result
            </h2>
            
            <div className={`status-badge status-${predictionResult.label.toLowerCase()}`}>
              {getStatusIcon(predictionResult.label)}
              {predictionResult.label}
            </div>

            <div style={{ width: '100%', textAlign: 'left', marginTop: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1.5rem' }}>
                <div style={{ height: '1px', flex: 1, background: 'var(--glass-border)' }}></div>
                <h3 style={{ margin: '0 1rem', color: '#cbd5e1', fontSize: '1.1rem' }}>Extracted Features</h3>
                <div style={{ height: '1px', flex: 1, background: 'var(--glass-border)' }}></div>
              </div>

              <div className="features-grid">
                {predictionResult.features && Object.entries(predictionResult.features).map(([key, value]) => (
                  <div className="feature-item" key={key}>
                    <span className="feature-label">{formatFeatureName(key)}</span>
                    <span className="feature-value">
                      {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(4)) : value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* View 2: Get Suggestions */}
        {activeView === 'suggestions' && suggestionResult && (
          <div style={{ animation: 'fadeIn 0.5s ease' }}>
            <SuggestionPanel 
              suggestions={suggestionResult.suggestions} 
              score={suggestionResult.score} 
            />
          </div>
        )}

        {/* View 3: Continuous Monitoring */}
        {activeView === 'monitoring' && monitoringStatus.isMonitoring && (
          <div style={{ animation: 'fadeIn 0.5s ease' }}>
            <MonitoringPanel 
              contractHash={monitoringStatus.hash}
              isMonitoring={monitoringStatus.isMonitoring}
            />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
