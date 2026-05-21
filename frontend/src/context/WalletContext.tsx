import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { PeraWalletConnect } from '@perawallet/connect';

// Initialize PeraWallet instance
const peraWallet = new PeraWalletConnect();

interface WalletContextType {
  walletAddress: string | null;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => Promise<void>;
  isConnecting: boolean;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

export const WalletProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [walletAddress, setWalletAddress] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('algoshield_test_wallet') || null;
    }
    return null;
  });
  const [isConnecting, setIsConnecting] = useState(false);

  useEffect(() => {
    // Check if test wallet is already seeded
    const seeded = localStorage.getItem('algoshield_test_wallet');
    if (seeded) {
      setWalletAddress(seeded);
      return;
    }

    // Reconnect session on component mount
    peraWallet.reconnectSession().then((accounts) => {
      // Setup disconnect event listener
      peraWallet.connector?.on('disconnect', () => { disconnectWallet(); });

      if (accounts.length) {
        setWalletAddress(accounts[0]);
      }
    }).catch(console.error);

    return () => {
      peraWallet.connector?.off('disconnect', () => { disconnectWallet(); });
    };
  }, []);

  const connectWallet = async () => {
    try {
      setIsConnecting(true);
      const accounts = await peraWallet.connect();
      // Setup disconnect event listener
      peraWallet.connector?.on('disconnect', () => { disconnectWallet(); });

      if (accounts.length) {
        setWalletAddress(accounts[0]);
      }
    } catch (error: any) {
      if (error?.data?.type !== "CONNECT_MODAL_CLOSED") {
        console.error("Connection failed", error);
      }
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectWallet = async () => {
    try {
      await peraWallet.disconnect();
    } catch (e) {}
    localStorage.removeItem('algoshield_test_wallet');
    setWalletAddress(null);
  };

  return (
    <WalletContext.Provider value={{ walletAddress, connectWallet, disconnectWallet, isConnecting }}>
      {children}
    </WalletContext.Provider>
  );
};

export const useWallet = () => {
  const context = useContext(WalletContext);
  if (context === undefined) {
    throw new Error('useWallet must be used within a WalletProvider');
  }
  return context;
};

