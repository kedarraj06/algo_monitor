import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { useWallet } from '../context/WalletContext';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, UploadCloud, Search, ShieldAlert } from 'lucide-react';
import { ScoreGauge } from '../components/ScoreGauge';
import { VulnerabilityCard } from '../components/VulnerabilityCard';
import { CodeViewer } from '../components/CodeViewer';
import { SuggestionPanel } from '../components/SuggestionPanel';
import { motion } from 'framer-motion';
import SpotlightCard from '../components/SpotlightCard';

export const Scanner = () => {
  const { walletAddress } = useWallet();
  const navigate = useNavigate();

  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [appId, setAppId] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [isMinting, setIsMinting] = useState(false);
  const [fileState, setFileState] = useState<File | null>(null);

  const [suggestions, setSuggestions] = useState<any>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const handleMint = async () => {
    setIsMinting(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/mint-certificate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scan_id: scanResult.scan_id,
          wallet_address: walletAddress
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Minting failed');
      alert(`Certificate Minted Successfully!\nAsset ID: ${data.asset_id}\nTxn ID: ${data.txn_id}`);
    } catch (e: any) {
      alert(`Minting error: ${e.message}`);
    } finally {
      setIsMinting(false);
    }
  };

  useEffect(() => {
    if (!walletAddress) {
      navigate('/');
    }
  }, [walletAddress, navigate]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFileState(e.dataTransfer.files[0]);
      runScan(e.dataTransfer.files[0]);
    }
  };

  const runScan = async (file?: File) => {
    setIsScanning(true);
    setScanResult(null);

    const formData = new FormData();
    formData.append('wallet_address', walletAddress || '');
    if (file) {
      formData.append('file', file);
    } else if (appId) {
      formData.append('app_id', appId);
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Scan failed');
      }

      const data = await response.json();
      setScanResult({
        ...data,
        vulnerabilities: data.vulnerabilities.map((v: any) => ({
          line: v.line || 0,
          issue: v.type || v.issue,
          severity: v.severity,
          suggestion: v.suggestion || "Review the flagged code block."
        }))
      });
    } catch (error) {
      console.error('Scan error:', error);
      alert('Failed to scan contract. Please try again.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleGetSuggestions = async () => {
    if (!scanResult) return;
    setLoadingSuggestions(true);
    setShowSuggestions(true);
    try {
      // Use scan_id if available, otherwise re-send the file
      const formData = new FormData();
      if (scanResult.scan_id) {
        formData.append('scan_id', scanResult.scan_id);
        formData.append('wallet_address', walletAddress || 'anonymous');
      } else if (fileState) {
        formData.append('file', fileState);
        formData.append('wallet_address', walletAddress || 'anonymous');
      }
      const res = await fetch('http://127.0.0.1:8000/suggest', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Suggestions failed');
      setSuggestions(data);
    } catch (err: any) {
      console.error('Suggestions error:', err.message);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  if (!walletAddress) return null;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 w-full">
        {!scanResult ? (
          <div className="max-w-3xl mx-auto mt-10">
            <div className="text-center mb-10">
              <h1 className="text-4xl font-syne font-bold mb-4">Smart Contract Scanner</h1>
              <p className="text-gray-400">Upload your .teal source or provide an Algorand App ID.</p>
            </div>

            <SpotlightCard className="shadow-2xl !p-0 relative overflow-hidden" spotlightColor="rgba(0, 255, 136, 0.15)">
              {isScanning ? (
                <div className="flex flex-col items-center justify-center py-20 text-center space-y-6">
                  <div className="relative">
                    <ShieldCheck className="w-20 h-20 text-primary animate-pulse-glow" />
                    <div className="absolute inset-0 rounded-full border-4 border-t-primary border-primary/20 animate-spin" />
                  </div>
                  <h3 className="text-2xl font-mono text-primary font-bold">ANALYZING CONTRACT...</h3>
                  <div className="font-mono text-gray-400 text-sm w-full max-w-xs text-left mx-auto">
                    <motion.p initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.5}}>&gt; Extracting AST...</motion.p>
                    <motion.p initial={{opacity:0}} animate={{opacity:1}} transition={{delay:1.2}}>&gt; Running pattern matching...</motion.p>
                    <motion.p initial={{opacity:0}} animate={{opacity:1}} transition={{delay:1.9}}>&gt; Calculating security score...</motion.p>
                  </div>
                </div>
              ) : (
                <div className="p-4 space-y-8">
                  {/* Drag & Drop Area */}
                  <div 
                    className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center transition-all ${dragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-gray-500'}`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                  >
                    <UploadCloud className={`w-16 h-16 ${dragActive ? 'text-primary' : 'text-gray-500'} mb-4`} />
                    <h3 className="text-xl font-syne font-bold mb-2">Drag & Drop .TEAL file here</h3>
                    <p className="text-gray-400 text-sm mb-4">Or click to browse from your computer.</p>
                    <label className="btn-secondary cursor-pointer">
                      Browse Files
                      <input type="file" className="hidden" accept=".teal,.py,.txt" onChange={(e) => {
                        if (e.target.files) {
                          setFileState(e.target.files[0]);
                          runScan(e.target.files[0]);
                        }
                      }} />
                    </label>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="h-px bg-border flex-1" />
                    <span className="text-gray-500 font-syne">OR</span>
                    <div className="h-px bg-border flex-1" />
                  </div>

                  {/* App ID Input */}
                  <div>
                    <label className="text-sm border-b-2 border-transparent font-mono text-gray-400 mb-2 block">Enter Algorand App ID:</label>
                    <div className="flex gap-4">
                      <div className="relative flex-1">
                        <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                        <input 
                          type="text" 
                          value={appId}
                          onChange={(e) => setAppId(e.target.value)}
                          placeholder="e.g. 1234567" 
                          className="w-full bg-surface border border-border rounded-lg pl-10 pr-4 py-3 text-white focus:outline-none focus:border-primary transition-colors font-mono"
                        />
                      </div>
                      <button onClick={runScan} disabled={!appId} className="btn-primary !py-3 whitespace-nowrap">
                        Run Security Scan
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </SpotlightCard>
          </div>
        ) : (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-10 duration-700">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-syne font-bold mb-2">Scan Results</h1>
                <p className="text-gray-400">Analysis complete. Review the findings below.</p>
              </div>
              
              <button onClick={() => setScanResult(null)} className="btn-secondary">
                Scan Another
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Score Summary */}
              <div className="lg:col-span-4 space-y-6">
                <SpotlightCard className="text-center relative overflow-hidden" spotlightColor="rgba(0, 255, 136, 0.2)">
                  <div className={`absolute top-0 left-0 right-0 h-1 ${scanResult.score > 70 ? 'bg-safe' : scanResult.score > 40 ? 'bg-warning' : 'bg-danger'}`} />
                  <h3 className="text-gray-400 font-syne font-bold text-lg mb-6">Security Score</h3>
                  
                  <ScoreGauge score={scanResult.score} />

                  <div className="mt-8 flex justify-center">
                    <div className={`flex items-center gap-2 px-4 py-2 border rounded-full font-mono font-bold
                      ${scanResult.risk_level === 'Safe' ? 'text-safe border-safe/50 bg-safe/10 shadow-[0_0_15px_rgba(0,255,136,0.3)]' : 
                        scanResult.risk_level === 'Risky' ? 'text-warning border-warning/50 bg-warning/10 shadow-[0_0_15px_rgba(255,170,0,0.3)]' : 
                        'text-danger border-danger/50 bg-danger/10 shadow-[0_0_15px_rgba(255,51,51,0.3)]'}
                    `}>
                      <ShieldAlert className="w-5 h-5" />
                      {scanResult.risk_level.toUpperCase()}
                    </div>
                  </div>

                  <div className="mt-8">
                    {scanResult.score > 70 ? (
                      <button 
                        onClick={handleMint}
                        disabled={isMinting}
                        className="btn-primary w-full shadow-[0_0_20px_rgba(0,255,136,0.5)] disabled:opacity-50"
                      >
                        {isMinting ? "Minting NFT on Algorand..." : "Mint NFT Certificate"}
                      </button>
                    ) : (
                      <button onClick={handleGetSuggestions} className="w-full bg-surface border border-warning text-warning hover:bg-warning hover:text-black font-bold py-3 px-6 rounded-lg transition-all duration-300">🧠 Get AI Suggestions</button>
                    )}
                  </div>
                </SpotlightCard>
                
                {/* Vulnerabilities List */}
                <SpotlightCard spotlightColor="rgba(255, 51, 51, 0.15)">
                  <h3 className="text-white font-syne font-bold text-xl mb-4 border-b border-border pb-2">Vulnerabilities</h3>
                  <motion.div 
                    initial="hidden" animate="visible"
                    variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
                    className="space-y-4"
                  >
                    {scanResult.vulnerabilities.map((v: any, i: number) => (
                      <VulnerabilityCard key={i} {...v} />
                    ))}
                  </motion.div>
                  {showSuggestions && (
                    <div style={{ marginTop: '1.5rem' }}>
                      {loadingSuggestions && (
                        <div style={{ color: '#64748b', padding: '1rem', textAlign: 'center' }}>
                          ⟳ Analyzing with AI model...
                        </div>
                      )}
                      {suggestions && !loadingSuggestions && (
                        <SuggestionPanel 
                          suggestions={suggestions.suggestions || []} 
                          score={suggestions.security_score} 
                          summary={suggestions.summary} 
                        />
                      )}
                    </div>
                  )}
                </SpotlightCard>
              </div>

              {/* Code Viewer */}
              <div className="lg:col-span-8 flex flex-col">
                <h3 className="text-white font-syne font-bold text-xl mb-4 pl-2">Contract Code</h3>
                <CodeViewer 
                  code={scanResult.contract_code} 
                  highlights={scanResult.vulnerabilities.map((v: any) => v.line)} 
                />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
