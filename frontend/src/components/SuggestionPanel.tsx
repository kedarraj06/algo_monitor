import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sparkles, Terminal, Copy, Check, Play, Pause, 
  FastForward, ShieldAlert, AlertTriangle, ShieldCheck, Info, ChevronRight
} from 'lucide-react';

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
  onFocusLine?: (line: number | null) => void;
  onStreamComplete?: () => void;
}

export const SuggestionPanel: React.FC<SuggestionPanelProps> = ({ 
  suggestions, 
  score, 
  summary,
  onFocusLine,
  onStreamComplete
}) => {
  // Streaming state machine
  const [currentSuggestIndex, setCurrentSuggestIndex] = useState(0);
  const [completedSuggestions, setCompletedSuggestions] = useState<Suggestion[]>([]);
  
  // Active streaming fields
  const [streamedVuln, setStreamedVuln] = useState('');
  const [streamedDesc, setStreamedDesc] = useState('');
  const [streamedFix, setStreamedFix] = useState('');
  const [activeField, setActiveField] = useState<'vulnerability' | 'description' | 'fix' | 'done'>('vulnerability');

  // Control settings
  const [isPaused, setIsPaused] = useState(false);
  const [speed, setSpeed] = useState<number>(30); // Milliseconds per word/chunk
  const [isCopied, setIsCopied] = useState<Record<number, boolean>>({});

  const containerRef = useRef<HTMLDivElement>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Restart streaming if suggestions change
  useEffect(() => {
    setCompletedSuggestions([]);
    setCurrentSuggestIndex(0);
    setStreamedVuln('');
    setStreamedDesc('');
    setStreamedFix('');
    setActiveField('vulnerability');
  }, [suggestions]);

  // Handle focusing code lines as suggestion changes
  useEffect(() => {
    if (suggestions && suggestions[currentSuggestIndex]) {
      const activeLine = suggestions[currentSuggestIndex].line;
      if (activeLine && onFocusLine) {
        onFocusLine(activeLine);
      }
    }
  }, [currentSuggestIndex, suggestions, onFocusLine]);

  // Main streaming tick
  useEffect(() => {
    if (isPaused || !suggestions || suggestions.length === 0 || currentSuggestIndex >= suggestions.length) {
      if (suggestions && suggestions.length > 0 && currentSuggestIndex >= suggestions.length) {
        onStreamComplete?.();
      }
      return;
    }

    const currentSugg = suggestions[currentSuggestIndex];
    
    // Split target texts into words/chunks
    const vulnWords = currentSugg.vulnerability.split(' ');
    const descWords = currentSugg.description.split(' ');
    
    // For fix code, we can stream line by line or word-by-word
    const fixWords = currentSugg.fix.split(' ');

    let wordIdx = 0;

    const streamNext = () => {
      if (activeField === 'vulnerability') {
        const currentWords = streamedVuln ? streamedVuln.split(' ') : [];
        if (currentWords.length < vulnWords.length) {
          const nextWord = vulnWords[currentWords.length];
          setStreamedVuln(prev => prev ? `${prev} ${nextWord}` : nextWord);
        } else {
          setActiveField('description');
        }
      } 
      
      else if (activeField === 'description') {
        const currentWords = streamedDesc ? streamedDesc.split(' ') : [];
        if (currentWords.length < descWords.length) {
          const nextWord = descWords[currentWords.length];
          setStreamedDesc(prev => prev ? `${prev} ${nextWord}` : nextWord);
        } else {
          setActiveField('fix');
        }
      } 
      
      else if (activeField === 'fix') {
        const currentWords = streamedFix ? streamedFix.split(' ') : [];
        if (currentWords.length < fixWords.length) {
          const nextWord = fixWords[currentWords.length];
          setStreamedFix(prev => prev ? `${prev} ${nextWord}` : nextWord);
        } else {
          // Finished this suggestion! Save it to completed and move to next
          const finishedItem = {
            ...currentSugg,
            vulnerability: streamedVuln,
            description: streamedDesc,
            fix: streamedFix
          };
          setCompletedSuggestions(prev => [...prev, finishedItem]);
          
          if (currentSuggestIndex + 1 < suggestions.length) {
            setCurrentSuggestIndex(prev => prev + 1);
            setStreamedVuln('');
            setStreamedDesc('');
            setStreamedFix('');
            setActiveField('vulnerability');
          } else {
            setCurrentSuggestIndex(suggestions.length);
            setActiveField('done');
            onStreamComplete?.();
          }
        }
      }
    };

    intervalRef.current = setInterval(streamNext, speed);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [
    currentSuggestIndex, 
    activeField, 
    suggestions, 
    isPaused, 
    speed, 
    streamedVuln, 
    streamedDesc, 
    streamedFix,
    onStreamComplete
  ]);

  // Handle auto-scroll as content grows
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [streamedDesc, streamedFix, completedSuggestions]);

  const handleCopy = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setIsCopied(prev => ({ ...prev, [index]: true }));
      setTimeout(() => {
        setIsCopied(prev => ({ ...prev, [index]: false }));
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const skipStreaming = () => {
    if (!suggestions) return;
    setCompletedSuggestions(suggestions);
    setCurrentSuggestIndex(suggestions.length);
    setActiveField('done');
    onStreamComplete?.();
    if (onFocusLine && suggestions.length > 0) {
      onFocusLine(suggestions[suggestions.length - 1].line || 1);
    }
  };

  const getSeverityStyles = (severity: string) => {
    const s = severity.toUpperCase();
    if (s === 'CRITICAL') {
      return {
        border: 'border-l-danger/80 border-danger/20',
        text: 'text-danger',
        bg: 'bg-danger/5',
        badge: 'border-danger/40 text-danger bg-danger/10 shadow-[0_0_10px_rgba(255,51,51,0.2)]',
        icon: AlertTriangle
      };
    } else if (s === 'HIGH') {
      return {
        border: 'border-l-warning/80 border-warning/20',
        text: 'text-warning',
        bg: 'bg-warning/5',
        badge: 'border-warning/40 text-warning bg-warning/10 shadow-[0_0_10px_rgba(255,170,0,0.2)]',
        icon: ShieldAlert
      };
    } else if (s === 'MEDIUM') {
      return {
        border: 'border-l-yellow-500/80 border-yellow-500/20',
        text: 'text-yellow-500',
        bg: 'bg-yellow-500/5',
        badge: 'border-yellow-500/40 text-yellow-500 bg-yellow-500/10',
        icon: Info
      };
    }
    return {
      border: 'border-l-blue-500/80 border-blue-500/20',
      text: 'text-blue-400',
      bg: 'bg-blue-500/5',
      badge: 'border-blue-500/40 text-blue-400 bg-blue-500/10',
      icon: ShieldCheck
    };
  };

  const scoreColor = score >= 70 ? 'text-safe' : score >= 40 ? 'text-warning' : 'text-danger';
  const isCurrentlyStreaming = activeField !== 'done' && currentSuggestIndex < suggestions.length;

  if (!suggestions || suggestions.length === 0) {
    return (
      <div className="mt-6 p-8 bg-surface border border-border rounded-xl text-center shadow-lg backdrop-blur-md relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-r from-safe/5 via-transparent to-safe/5 opacity-50" />
        <div className="relative z-10">
          <span className="text-5xl block mb-4 animate-bounce">🛡️</span>
          <h3 className="text-safe text-2xl font-syne font-bold mb-2">Smart Contract is Secure</h3>
          <p className="text-gray-400 max-w-lg mx-auto">
            Our AI Security model analyzed this TEAL contract and did not detect any known high-risk vulnerability patterns. Standard assertion criteria have been verified!
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 rounded-xl border border-border bg-[#050505] shadow-2xl relative overflow-hidden flex flex-col max-h-[650px] transition-all duration-300">
      {/* Glow effect */}
      {isCurrentlyStreaming && (
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary via-secondary to-primary animate-shimmer" />
      )}

      {/* Terminal Assistant Header */}
      <div className="sticky top-0 bg-[#080808]/90 border-b border-border px-4 py-3 flex flex-wrap items-center justify-between z-20 backdrop-blur-md gap-3">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Sparkles className="w-5 h-5 text-primary animate-pulse-glow" />
            {isCurrentlyStreaming && (
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-primary rounded-full animate-ping" />
            )}
          </div>
          <div>
            <h3 className="text-white font-syne font-bold text-sm tracking-wide flex items-center gap-2">
              AlgoShield Security Assistant
            </h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-1.5 h-1.5 rounded-full ${isCurrentlyStreaming ? 'bg-primary animate-pulse-live' : 'bg-gray-500'}`} />
              <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">
                {isCurrentlyStreaming ? 'Live Auditing Contract' : 'Analysis Complete'}
              </span>
            </div>
          </div>
        </div>

        {/* Streaming Speed and Playback Controls */}
        <div className="flex items-center gap-2 bg-surface border border-border/80 px-2 py-1 rounded-lg">
          {isCurrentlyStreaming && (
            <>
              <button 
                onClick={() => setIsPaused(!isPaused)} 
                className="p-1.5 text-gray-400 hover:text-white rounded transition-colors"
                title={isPaused ? "Resume Analysis" : "Pause Analysis"}
              >
                {isPaused ? <Play className="w-3.5 h-3.5 text-primary" /> : <Pause className="w-3.5 h-3.5" />}
              </button>

              <button 
                onClick={() => setSpeed(prev => prev === 30 ? 10 : prev === 10 ? 1 : 30)} 
                className="p-1.5 text-gray-400 hover:text-white rounded transition-colors flex items-center gap-1"
                title="Adjust Streaming Speed"
              >
                <FastForward className="w-3.5 h-3.5" />
                <span className="text-[10px] font-mono font-bold">
                  {speed === 30 ? '1x' : speed === 10 ? '2x' : '⚡'}
                </span>
              </button>

              <button 
                onClick={skipStreaming} 
                className="text-[10px] font-mono font-bold bg-white/10 hover:bg-white/20 text-white px-2.5 py-1 rounded transition-colors"
              >
                SKIP
              </button>
            </>
          )}

          {!isCurrentlyStreaming && (
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-gray-400">Score:</span>
              <span className={`font-mono font-bold text-xs ${scoreColor}`}>{score}/100</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Analysis Log (Scrollable) */}
      <div 
        ref={containerRef}
        className="flex-grow p-4 md:p-6 overflow-y-auto space-y-6 scroll-smooth bg-gradient-to-b from-transparent to-black/30"
      >
        {/* Enriched Global Score Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border border-border/60 bg-white/[0.02] backdrop-blur-sm relative overflow-hidden group">
          <div className="absolute inset-y-0 left-0 w-1 bg-primary" />
          <div>
            <span className="text-[10px] font-mono text-primary uppercase tracking-widest block mb-1">Audit Overview</span>
            <h4 className="text-gray-200 font-syne font-bold text-lg leading-snug">
              {summary}
            </h4>
          </div>
          <div className="flex items-center gap-3 bg-black/40 border border-border px-4 py-2 rounded-lg shrink-0">
            <span className="text-xs font-mono text-gray-400">AI Security Score</span>
            <div className={`text-2xl font-mono font-bold ${scoreColor}`}>
              {score}/100
            </div>
          </div>
        </div>

        {/* Suggestions List */}
        <div className="space-y-6">
          <AnimatePresence>
            {/* Completed Suggestions */}
            {completedSuggestions.map((s, i) => {
              const styles = getSeverityStyles(s.severity);
              const SeverityIcon = styles.icon;
              return (
                <motion.div 
                  key={`completed-${i}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`bg-white/[0.01] border ${styles.border} border-l-4 rounded-xl p-5 hover:bg-white/[0.02] transition-colors`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3">
                      <SeverityIcon className={`w-5 h-5 ${styles.text}`} />
                      <h4 className="font-syne font-bold text-white text-base md:text-lg">
                        {s.vulnerability}
                      </h4>
                    </div>
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => onFocusLine?.(s.line || 1)}
                        className="bg-black/30 hover:bg-black/50 border border-border rounded px-2.5 py-1 text-xs text-gray-400 hover:text-primary font-mono transition-colors"
                      >
                        Line {s.line || 'N/A'}
                      </button>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono border uppercase tracking-wider font-bold ${styles.badge}`}>
                        {s.severity}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <span className="text-[10px] font-mono text-gray-500 uppercase tracking-wider block mb-1">Vulnerability Analysis</span>
                      <p className="text-gray-300 text-sm leading-relaxed">{s.description}</p>
                    </div>

                    {s.fix && (
                      <div className="border border-safe/25 bg-safe/5 rounded-xl overflow-hidden shadow-[0_0_15px_rgba(0,255,136,0.03)]">
                        <div className="bg-safe/10 border-b border-safe/20 px-4 py-2 flex items-center justify-between">
                          <span className="text-[10px] font-mono text-safe font-bold tracking-wider">RECOMMENDED SECURER IMPLEMENTATION</span>
                          <button 
                            onClick={() => handleCopy(s.fix, i)}
                            className="text-gray-400 hover:text-safe flex items-center gap-1.5 text-xs transition-colors py-0.5 px-2 rounded hover:bg-safe/10"
                          >
                            {isCopied[i] ? <Check className="w-3.5 h-3.5 text-safe" /> : <Copy className="w-3.5 h-3.5" />}
                            <span className="font-mono text-[10px]">{isCopied[i] ? 'Copied' : 'Copy'}</span>
                          </button>
                        </div>
                        <pre className="p-4 text-safe font-mono text-xs md:text-sm whitespace-pre-wrap overflow-x-auto leading-relaxed max-h-[250px] overflow-y-auto">
                          <code>{s.fix}</code>
                        </pre>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}

            {/* Currently Streaming Suggestion */}
            {isCurrentlyStreaming && (
              <motion.div 
                key={`streaming-${currentSuggestIndex}`}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                className={`bg-white/[0.01] border ${getSeverityStyles(suggestions[currentSuggestIndex].severity).border} border-l-4 rounded-xl p-5 relative overflow-hidden`}
              >
                {/* Background scanning line effect */}
                <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent opacity-30 h-10 animate-pulse" />

                <div className="flex flex-wrap items-center justify-between gap-3 mb-4 relative z-10">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-primary animate-pulse" />
                    <h4 className="font-syne font-bold text-white text-base md:text-lg">
                      {streamedVuln}
                      {activeField === 'vulnerability' && (
                        <span className="text-primary animate-pulse font-mono ml-1">█</span>
                      )}
                    </h4>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="bg-black/30 border border-border rounded px-2.5 py-1 text-xs text-gray-400 font-mono">
                      Line {suggestions[currentSuggestIndex].line || 'N/A'}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono border uppercase tracking-wider font-bold ${getSeverityStyles(suggestions[currentSuggestIndex].severity).badge}`}>
                      {suggestions[currentSuggestIndex].severity}
                    </span>
                  </div>
                </div>

                <div className="space-y-4 relative z-10">
                  {/* Description stream */}
                  {(streamedDesc || activeField === 'description') && (
                    <div>
                      <span className="text-[10px] font-mono text-primary/70 uppercase tracking-wider block mb-1">Vulnerability Analysis</span>
                      <p className="text-gray-300 text-sm leading-relaxed">
                        {streamedDesc}
                        {activeField === 'description' && (
                          <span className="text-primary animate-pulse font-mono ml-1">█</span>
                        )}
                      </p>
                    </div>
                  )}

                  {/* Fix code stream */}
                  {(streamedFix || activeField === 'fix') && (
                    <div className="border border-primary/25 bg-primary/5 rounded-xl overflow-hidden">
                      <div className="bg-primary/10 border-b border-primary/20 px-4 py-2 flex items-center justify-between">
                        <span className="text-[10px] font-mono text-primary font-bold tracking-wider">GENERATING FIX...</span>
                      </div>
                      <pre className="p-4 text-primary font-mono text-xs md:text-sm whitespace-pre-wrap overflow-x-auto leading-relaxed max-h-[250px] overflow-y-auto">
                        <code>
                          {streamedFix}
                          {activeField === 'fix' && (
                            <span className="text-primary animate-pulse font-mono ml-1">█</span>
                          )}
                        </code>
                      </pre>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Footer Info */}
      <div className="bg-[#080808]/90 border-t border-border px-4 py-2.5 flex items-center justify-between text-[10px] font-mono text-gray-500 z-10 backdrop-blur-md">
        <span>Model: Phi-3-mini Smart Contract Auditor</span>
        <span>Status: {isCurrentlyStreaming ? 'Typing suggestions...' : 'Completed successfully✓'}</span>
      </div>
    </div>
  );
};
