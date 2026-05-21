import React, { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { useWallet } from '../context/WalletContext';
import { useNavigate } from 'react-router-dom';
import { Award, ExternalLink, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';
import SpotlightCard from '../components/SpotlightCard';

export const Certificates = () => {
  const { walletAddress } = useWallet();
  const navigate = useNavigate();

  const [certs, setCerts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (walletAddress) {
      fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/certificates/${walletAddress}`)
        .then(res => res.json())
        .then(data => {
          setCerts(data);
          setIsLoading(false);
        })
        .catch(err => {
          console.error(err);
          setIsLoading(false);
        });
    } else {
      navigate('/');
    }
  }, [walletAddress, navigate]);

  return (
    <div className="min-h-screen flex flex-col bg-background relative">
      <Navbar />

      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 w-full min-h-screen relative z-10">
        <div className="mb-12">
          <h1 className="text-4xl font-syne font-bold mb-2">My Certificates</h1>
          <p className="text-gray-400">Verifiable on-chain proofs of security for your smart contracts.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {isLoading ? (
            <p className="text-gray-400">Loading certificates...</p>
          ) : certs.length === 0 ? (
            <p className="text-gray-400">No certificates minted yet.</p>
          ) : (
            certs.map((cert, index) => (
              <motion.div 
                key={cert.cert_id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className=""
              >
                <SpotlightCard className="relative rounded-2xl overflow-hidden !p-0 border-safe/30 group hover:border-safe/80" spotlightColor="rgba(0, 255, 136, 0.2)">
                  <div className="bg-safe/10 h-32 relative flex justify-center items-center">
                    <div className="absolute top-4 right-4 bg-background/50 backdrop-blur-sm px-3 py-1 rounded-full text-xs font-mono text-safe font-bold font-syne shadow-[0_0_10px_rgba(0,255,136,0.3)]">
                      Score: {cert.score}
                    </div>
                    <Award className="w-16 h-16 text-safe opacity-20 absolute" />
                    <ShieldCheck className="w-12 h-12 text-safe drop-shadow-[0_0_10px_rgba(0,255,136,0.8)] z-10" />
                  </div>
                  
                  <div className="p-6">
                    <h3 className="font-syne font-bold text-xl mb-1 text-white">{cert.filename || `App ID: ${cert.app_id || 'Unknown'}`}</h3>
                    <p className="text-gray-400 text-sm font-mono mb-6">Txn: {cert.txn_id.slice(0, 16)}...</p>
                    
                    <div className="space-y-2 mb-6">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Date Minted</span>
                        <span className="text-gray-300 font-mono">{new Date(cert.minted_at).toLocaleDateString()}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Asset ID</span>
                        <span className="text-gray-300 font-mono">{cert.asset_id}</span>
                      </div>
                    </div>
  
                    <a 
                      href={cert.explorer_url}
                      target="_blank" 
                      rel="noreferrer"
                      className="w-full btn-secondary text-sm !py-2 flex justify-center gap-2 group-hover:bg-safe group-hover:text-black group-hover:border-safe"
                    >
                      View on Pera Explorer <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 border-2 border-yellow-500/30 w-full h-[150%] rotate-3 pointer-events-none hidden group-hover:block transition-all opacity-10 blur-sm" />
                </SpotlightCard>
              </motion.div>
            ))
          )}
        </div>
      </main>
    </div>
  );
};
