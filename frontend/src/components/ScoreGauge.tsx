import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export const ScoreGauge = ({ score }: { score: number }) => {
  const [currentScore, setCurrentScore] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = score;
    if (start === end) return;
    
    let totalDuration = 2000;
    let incrementTime = (totalDuration / end);

    let timer = setInterval(() => {
      start += 1;
      setCurrentScore(start);
      if (start === end) clearInterval(timer);
    }, incrementTime);

    return () => clearInterval(timer);
  }, [score]);

  let colorStr = '#ff3333';
  let colorName = 'danger';
  let shadowStr = 'rgba(255,51,51,0.5)';
  
  if (score > 70) {
    colorStr = '#00ff88';
    colorName = 'safe';
    shadowStr = 'rgba(0,255,136,0.5)';
  } else if (score > 40) {
    colorStr = '#ffaa00';
    colorName = 'warning';
    shadowStr = 'rgba(255,170,0,0.5)';
  }

  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (currentScore / 100) * circumference;

  return (
    <div className="relative flex justify-center items-center w-48 h-48 mx-auto">
      <svg className="transform -rotate-90 w-full h-full" viewBox="0 0 140 140">
        <circle 
          cx="70" cy="70" r={radius} 
          fill="transparent" 
          stroke="rgba(255,255,255,0.1)" 
          strokeWidth="10" 
        />
        <circle 
          cx="70" cy="70" r={radius} 
          fill="transparent" 
          stroke={colorStr} 
          strokeWidth="10" 
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-100 ease-out"
          style={{ filter: `drop-shadow(0 0 8px ${shadowStr})` }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className={`text-4xl font-syne font-bold tracking-tighter`} style={{ color: colorStr }}>
          {currentScore}
        </span>
        <span className="text-xs text-gray-400 font-mono mt-1">/100</span>
      </div>
    </div>
  );
};
