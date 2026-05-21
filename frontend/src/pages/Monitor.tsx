import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { useWallet } from '../context/WalletContext';
import { useNavigate } from 'react-router-dom';
import { Activity, Shield, Hash, ShieldAlert, Mail, Send } from 'lucide-react';
import { motion } from 'framer-motion';
import { AlertBanner } from '../components/AlertBanner';
import SpotlightCard from '../components/SpotlightCard';

export const Monitor = () => {
  const { walletAddress } = useWallet();
  const navigate = useNavigate();
  
  const [appId, setAppId] = useState('');
  const [accountAddr, setAccountAddr] = useState('');
  const [alertEmail, setAlertEmail] = useState('');
  const [telegramChatId, setTelegramChatId] = useState('');
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [showAlertBanner, setShowAlertBanner] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  const [healthExplanation, setHealthExplanation] = useState<string | null>(null);

  useEffect(() => {
    if (!walletAddress) {
      navigate('/');
    }
  }, [walletAddress, navigate]);

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
  const WS_URL = API_URL.replace('http://', 'ws://').replace('https://', 'wss://');

  let timeoutId: any;
  const startMonitoring = async () => {
    if (!appId) return;
    try {
      const res = await fetch(`${API_URL}/monitor/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_address: walletAddress,
          app_id: parseInt(appId),
          account_address: accountAddr || '',
          alert_email: alertEmail || null,
          telegram_chat_id: telegramChatId || null
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Start failed');
      
      setJobId(data.job_id);
      setIsMonitoring(true);
      setHealthStatus(data.initial_status || 'SAFE');
      setHealthExplanation(data.explanation || 'Baseline scan established.');
      setAlerts([]);
    } catch (e: any) {
      alert(`Failed to start monitoring: ${e.message}`);
    }
  };

  const stopMonitoring = async () => {
    setIsMonitoring(false);
    if (jobId) {
      try {
        await fetch(`${API_URL}/monitor/stop/${jobId}`, {
          method: 'POST'
        });
      } catch (e) {}
    }
    setJobId(null);
    setHealthStatus(null);
    setHealthExplanation(null);
  };

  useEffect(() => {
    let ws: WebSocket | null = null;
    let interval: any;

    if (isMonitoring && appId) {
      // 1. Fetch existing alerts from DB
      const fetchHistory = async () => {
        try {
          const res = await fetch(`${API_URL}/monitor/${appId}/alerts?wallet_address=${walletAddress}`);
          const data = await res.json();
          if (res.ok && data.alerts && data.alerts.length > 0) {
            setAlerts(data.alerts.map((a: any) => ({
              timestamp: new Date(a.timestamp).toLocaleTimeString(),
              type: (a.severity || 'SAFE') + ' Alert',
              description: a.description,
              severity: a.severity || 'SAFE',
              score: a.anomaly_score,
            })));
            
            // Extract baseline status from history
            const latestAlert = data.alerts[data.alerts.length - 1]; // Baseline is the first inserted (oldest in time, last in list) or latest
            const monitorStartAlert = data.alerts.find((a: any) => a.description && a.description.includes("Monitoring Started"));
            if (monitorStartAlert) {
              const cleanedDesc = monitorStartAlert.description.replace(/Monitoring Started\s*—\s*[A-Z_ ]+:\s*/i, "");
              setHealthStatus(monitorStartAlert.severity || 'SAFE');
              setHealthExplanation(cleanedDesc || 'Monitoring Started successfully.');
            } else if (latestAlert) {
              setHealthStatus(latestAlert.severity || 'SAFE');
              setHealthExplanation(latestAlert.description || 'Monitoring Active.');
            }
          }
        } catch (e) {
          console.error('History fetch error', e);
        }
      };
      fetchHistory();

      // 2. WebSocket for real-time events (all severities come through)
      ws = new WebSocket(`${WS_URL}/monitor/ws/${appId}`);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const sev = (data.severity || 'SAFE').toUpperCase();
          const newAlert = {
            timestamp: new Date().toLocaleTimeString(),
            type: sev + ' Alert',
            description: data.description || 'Transaction detected',
            severity: sev,
            score: data.score,
          };
          setAlerts(prev => [newAlert, ...prev.slice(0, 49)]); // cap at 50
          // Only flash banner for HIGH risk
          if (sev === 'HIGH') {
            setShowAlertBanner(true);
            setTimeout(() => setShowAlertBanner(false), 5000);
          }
        } catch (e) {
          console.error('WebSocket parse error', e);
        }
      };

      ws.onerror = (e) => console.error('WebSocket error', e);

      // 30s fallback polling if WebSocket drops
      interval = setInterval(fetchHistory, 30000);
    }
    return () => {
      if (ws) ws.close();
      if (interval) clearInterval(interval);
    };
  }, [isMonitoring, appId, walletAddress]);

  if (!walletAddress) return null;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />
      
      <AlertBanner 
        show={showAlertBanner} 
        message="A potential Reentrancy attack was just detected logic execution on App ID." 
      />

      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 w-full">
        <div className="mb-12 flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-syne font-bold mb-2 flex items-center gap-4">
              Live Monitoring
              {isMonitoring && (
                 <span className="flex items-center gap-2 text-sm bg-safe/10 border border-safe text-safe px-3 py-1 rounded-full animate-pulse shadow-[0_0_10px_rgba(0,255,136,0.5)]">
                   <span className="w-2 h-2 rounded-full bg-safe"></span>
                   ACTIVE
                 </span>
              )}
            </h1>
            <p className="text-gray-400">Set up 24/7 AI-powered anomaly detection for live smart contracts.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Config Card */}
          <div className="lg:col-span-1 space-y-6">
            <SpotlightCard spotlightColor="rgba(0, 212, 255, 0.15)">
              <h3 className="font-syne font-bold text-xl mb-4 border-b border-border pb-2 flex items-center gap-2">
                <Shield className="w-5 h-5 text-secondary" />
                Target Setup
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-mono text-gray-400 mb-1 block">Algorand App ID:</label>
                  <div className="relative">
                    <Hash className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input 
                      type="text" 
                      value={appId}
                      onChange={(e) => setAppId(e.target.value)}
                      disabled={isMonitoring}
                      className="w-full bg-background border border-border rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-secondary transition-colors font-mono disabled:opacity-50"
                      placeholder="e.g. 1234567"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-mono text-gray-400 mb-1 block">Monitor Account (Optional):</label>
                  <div className="relative">
                    <Activity className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input 
                      type="text" 
                      value={accountAddr}
                      onChange={(e) => setAccountAddr(e.target.value)}
                      disabled={isMonitoring}
                      className="w-full bg-background border border-border rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-secondary transition-colors font-mono disabled:opacity-50"
                      placeholder="e.g. ABCDE...1234"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-mono text-gray-400 mb-1 block">Alert Email (Optional):</label>
                  <div className="relative">
                    <Mail className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input 
                      type="email" 
                      value={alertEmail}
                      onChange={(e) => setAlertEmail(e.target.value)}
                      disabled={isMonitoring}
                      className="w-full bg-background border border-border rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-secondary transition-colors font-mono disabled:opacity-50"
                      placeholder="e.g. security@team.com"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-mono text-gray-400 mb-1 block">Telegram Chat ID (Optional):</label>
                  <div className="relative">
                    <Send className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input 
                      type="text" 
                      value={telegramChatId}
                      onChange={(e) => setTelegramChatId(e.target.value)}
                      disabled={isMonitoring}
                      className="w-full bg-background border border-border rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-secondary transition-colors font-mono disabled:opacity-50"
                      placeholder="e.g. 123456789"
                    />
                  </div>
                </div>

                <div className="pt-4">
                  {!isMonitoring ? (
                    <button 
                      onClick={startMonitoring}
                      disabled={!appId} 
                      className="btn-primary w-full disabled:opacity-50 !bg-secondary !text-black hover:!shadow-[0_0_20px_rgba(0,212,255,0.4)]"
                    >
                      Start Monitoring
                    </button>
                  ) : (
                    <button 
                      onClick={stopMonitoring}
                      className="w-full bg-danger/20 border border-danger text-danger font-bold py-3 px-6 rounded-lg transition-all duration-300 hover:bg-danger hover:text-white"
                    >
                      Stop Monitoring
                    </button>
                  )}
                </div>
              </div>
            </SpotlightCard>
          </div>

          {/* Live Feed */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {isMonitoring && healthStatus && (
              <motion.div 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <SpotlightCard spotlightColor={
                  healthStatus === 'SAFE' ? 'rgba(0, 255, 136, 0.15)' :
                  healthStatus === 'LOW RISK' ? 'rgba(0, 212, 255, 0.15)' :
                  healthStatus === 'WARNING' || healthStatus === 'SUSPICIOUS' ? 'rgba(255, 187, 0, 0.15)' :
                  'rgba(255, 77, 77, 0.15)'
                }>
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <h4 className="text-xs font-mono text-gray-400 mb-1.5 uppercase tracking-wider">Contract Security Status</h4>
                      <div className="flex flex-wrap items-center gap-3">
                        <span className={`text-sm font-bold font-mono px-3 py-1 rounded-full ${
                          healthStatus === 'SAFE' ? 'bg-safe/10 border border-safe text-safe shadow-[0_0_10px_rgba(0,255,136,0.3)]' :
                          healthStatus === 'LOW RISK' ? 'bg-secondary/10 border border-secondary text-secondary shadow-[0_0_10px_rgba(0,212,255,0.3)]' :
                          healthStatus === 'WARNING' || healthStatus === 'SUSPICIOUS' ? 'bg-warning/10 border border-warning text-warning shadow-[0_0_10px_rgba(255,187,0,0.3)]' :
                          'bg-danger/10 border border-danger text-danger shadow-[0_0_10px_rgba(255,77,77,0.3)] animate-pulse'
                        }`}>
                          ● {healthStatus}
                        </span>
                        <p className="text-white text-sm font-syne font-medium">{healthExplanation}</p>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-xs font-mono text-gray-500">Scan established on start</span>
                    </div>
                  </div>
                </SpotlightCard>
              </motion.div>
            )}

            <SpotlightCard className="flex-grow min-h-[500px] flex flex-col" spotlightColor="rgba(0, 255, 136, 0.15)">
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-syne font-bold text-xl flex items-center gap-2">
                  <Activity className="w-5 h-5 text-primary" />
                  Live Activity Feed
                </h3>
                {isMonitoring && (
                  <span className="text-sm font-mono text-gray-400 flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-primary animate-ping inline-block"></span>
                    Polling every 5s...
                  </span>
                )}
              </div>

              <div className="flex-grow bg-background/50 rounded-xl border border-border p-4 overflow-y-auto">
                {!isMonitoring && alerts.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
                    <Activity className="w-16 h-16 opacity-20" />
                    <p className="font-mono">Monitoring is not active.</p>
                  </div>
                ) : alerts.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <p className="font-mono text-primary text-sm">Listening for transactions on App {appId}...</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {alerts.map((alert, idx) => {
                      const sev = (alert.severity || 'SAFE').toUpperCase();
                      const isHigh = sev === 'HIGH';
                      const isWarning = sev === 'WARNING';
                      const isSafe = !isHigh && !isWarning;
                      return (
                        <motion.div
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          key={idx}
                          className={`p-4 rounded-lg border flex gap-4 ${
                            isHigh
                              ? 'bg-red-900/20 border-red-500/50 text-red-300'
                              : isWarning
                              ? 'bg-yellow-900/20 border-yellow-500/50 text-yellow-300'
                              : 'bg-green-900/10 border-green-700/30 text-green-400'
                          }`}
                        >
                          <ShieldAlert className={`w-6 h-6 shrink-0 mt-1 ${
                            isHigh ? 'text-red-400' : isWarning ? 'text-yellow-400' : 'text-green-500'
                          }`} />
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-start mb-1 gap-2">
                              <div className="flex items-center gap-2">
                                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                                  isHigh ? 'bg-red-500/20 text-red-300' :
                                  isWarning ? 'bg-yellow-500/20 text-yellow-300' :
                                  'bg-green-500/20 text-green-400'
                                }`}>{sev}</span>
                                <h4 className="font-syne font-bold text-sm truncate">{alert.type || sev + ' Alert'}</h4>
                              </div>
                              <span className="font-mono text-xs opacity-60 shrink-0">{alert.timestamp}</span>
                            </div>
                            <p className="text-xs opacity-80 leading-relaxed">{alert.description}</p>
                            {alert.score !== undefined && (
                              <div className="mt-2 flex items-center gap-2">
                                <div className="flex-1 bg-black/30 rounded-full h-1.5">
                                  <div
                                    className={`h-1.5 rounded-full transition-all ${
                                      isHigh ? 'bg-red-500' : isWarning ? 'bg-yellow-400' : 'bg-green-500'
                                    }`}
                                    style={{ width: `${Math.round((alert.score || 0) * 100)}%` }}
                                  />
                                </div>
                                <span className="text-xs font-mono opacity-60">{((alert.score || 0) * 100).toFixed(0)}%</span>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                )}
              </div>
            </SpotlightCard>
          </div>
        </div>
      </main>
    </div>
  );
};
