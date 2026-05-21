import React from 'react';

const MonitoringPanel = ({ contractHash, isMonitoring }) => {
  if (!isMonitoring) return null;

  return (
    <div className="glass-card result-container" style={{ marginTop: '2rem' }}>
      <h2 style={{ marginBottom: '1rem', color: '#fff', fontSize: '1.4rem', fontWeight: '600', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
        📡 Monitoring Dashboard
      </h2>
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ position: 'relative', width: '80px', height: '80px', margin: '0 auto 1.5rem auto' }}>
          {/* We'll use a simple CSS animation inline or defined in index.css */}
          <div style={{ position: 'absolute', inset: 0, border: '4px solid #3b82f6', borderRadius: '50%', borderTopColor: 'transparent', animation: 'spin 1.5s linear infinite' }}></div>
          <span style={{ fontSize: '32px', position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>📡</span>
        </div>
        <h3 style={{ color: '#60a5fa', fontSize: '1.4rem' }}>Monitoring Active</h3>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem', wordBreak: 'break-all' }}>
          Target: {contractHash}
        </p>
        <p style={{ color: 'var(--text-muted)', marginTop: '1rem', fontSize: '0.9rem' }}>
          The system is currently scanning network activity for suspicious transactions related to this contract. Alerts will appear here.
        </p>
      </div>
      
      <div style={{ width: '100%', textAlign: 'left', marginTop: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div style={{ height: '1px', flex: 1, background: 'var(--glass-border)' }}></div>
          <h3 style={{ margin: '0 1rem', color: '#cbd5e1', fontSize: '1.1rem' }}>Recent Alerts</h3>
          <div style={{ height: '1px', flex: 1, background: 'var(--glass-border)' }}></div>
        </div>
        <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
          <span style={{ color: 'var(--text-muted)' }}>No suspicious activity detected yet.</span>
        </div>
      </div>
    </div>
  );
};

export default MonitoringPanel;
