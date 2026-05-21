import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { WalletProvider, useWallet } from './context/WalletContext';
import { Landing } from './pages/Landing';
import { Dashboard } from './pages/Dashboard';
import { Scanner } from './pages/Scanner';
import { Certificates } from './pages/Certificates';
import { Monitor } from './pages/Monitor';
import Dither from './components/Dither';
import './styles/main.css';

const ProtectedRoute = () => {
  const { walletAddress } = useWallet();
  if (!walletAddress) {
    // If not connected, drop them safely back at the landing page
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
};

function AppContent() {
  return (
    <div style={{ position: 'relative', minHeight: '100vh', width: '100vw', backgroundColor: '#0a0a0a', color: '#fff', overflowX: 'hidden' }}>
      
      {/* Global Dither Background Effect */}
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 0, width: '100%', height: '100%', pointerEvents: 'auto', opacity: 0.9 }}>
         <Dither 
           waveColor={[0, 0.5, 0.15]} 
           colorNum={4} 
           disableAnimation={false} 
           enableMouseInteraction={true} 
           mouseRadius={0.4} 
           waveAmplitude={0.3} 
           waveFrequency={3} 
           waveSpeed={0.05} 
         />
      </div>

      {/* Foreground Content */}
      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', minHeight: '100vh', pointerEvents: 'none' }}>
        
        <main className="flex-1" style={{ pointerEvents: 'auto' }}>
          <Routes>
            <Route path="/" element={<Landing />} />
            
            {/* Protected Routes that require Pera Wallet */}
            <Route element={<ProtectedRoute />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/scan" element={<Scanner />} />
              <Route path="/certificates" element={<Certificates />} />
              <Route path="/monitor" element={<Monitor />} />
            </Route>

            {/* Fallback route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <WalletProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </WalletProvider>
  );
}
