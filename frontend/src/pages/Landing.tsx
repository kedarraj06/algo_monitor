import React from 'react';
import { Navbar } from '../components/Navbar';
import Dither from '../components/Dither';
import ASCIIText from '../components/ASCIIText';
import SpotlightCard from '../components/SpotlightCard';
import { AnimatedText } from '../components/AnimatedText';
import { ShieldAlert, Award, Activity } from 'lucide-react';
import { useWallet } from '../context/WalletContext';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

export const Landing = () => {
  const { walletAddress, connectWallet } = useWallet();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (walletAddress) {
      navigate('/dashboard');
    }
  }, [walletAddress, navigate]);

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Background with z-index under everything */}
      <div className="absolute inset-0 z-0">
        <Dither colorNum={4} pixelSize={2} waveColor={[0.0, 1.0, 0.53]} mouseRadius={1.5} />
      </div>
      
      <div className="absolute inset-0 z-[1] opacity-20 hidden md:block">
        <ASCIIText 
          text="ALGO_SHIELD" 
          asciiFontSize={12} 
          textFontSize={250} 
          enableWaves={true} 
        />
      </div>

      {/* Overlay to ensure text readability */}
      <div className="absolute inset-0 bg-background/70 z-[1]" />

      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />

        <main className="flex-grow flex flex-col justify-center items-center px-4 py-20">
          <div className="max-w-4xl w-full text-center space-y-12">
            <div className="space-y-6">
              <h1 className="text-5xl md:text-7xl font-syne font-bold leading-tight">
                <AnimatedText text="Securing Web3," className="justify-center text-white" />
                <AnimatedText text="One Contract at a Time" className="justify-center text-primary" />
              </h1>
              <p className="text-xl text-gray-400 font-sans max-w-2xl mx-auto">
                AI-powered smart contract security auditing for the Algorand blockchain. Scan, monitor, and certify your builds with terminal precision.
              </p>
            </div>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.5 }}
              className="flex flex-col sm:flex-row justify-center gap-4"
            >
              {!walletAddress && (
                <button onClick={connectWallet} className="btn-primary text-lg !py-4 !px-8 border border-primary shadow-[0_0_30px_rgba(0,255,136,0.1)] hover:shadow-[0_0_50px_rgba(0,255,136,0.5)]">
                  Connect Pera Wallet
                </button>
              )}
            </motion.div>

            <motion.div 
              className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 text-left"
              initial="hidden"
              animate="visible"
              variants={{
                hidden: {},
                visible: {
                  transition: { staggerChildren: 0.2, delayChildren: 1.2 }
                }
              }}
            >
              {/* Feature 1 */}
              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
                <SpotlightCard className="h-full" spotlightColor="rgba(0, 212, 255, 0.2)">
                  <ShieldAlert className="w-12 h-12 text-secondary mb-4 drop-shadow-[0_0_10px_rgba(0,212,255,0.8)]" />
                  <h3 className="text-2xl font-syne font-bold mb-2">Smart Contract Scanner</h3>
                  <p className="text-gray-400 text-sm">Upload your .teal or point to an App ID for an instant line-by-line AI vulnerability analysis.</p>
                </SpotlightCard>
              </motion.div>

              {/* Feature 2 */}
              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
                <SpotlightCard className="border-t border-primary/50 h-full" spotlightColor="rgba(255, 170, 0, 0.2)">
                  <Award className="w-12 h-12 text-warning mb-4 drop-shadow-[0_0_10px_rgba(255,170,0,0.8)]" />
                  <h3 className="text-2xl font-syne font-bold mb-2">NFT Security Certificate</h3>
                  <p className="text-gray-400 text-sm">Pass the audit with a high score and automatically mint a verifiable on-chain proof of security.</p>
                </SpotlightCard>
              </motion.div>

              {/* Feature 3 */}
              <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
                <SpotlightCard className="h-full" spotlightColor="rgba(0, 255, 136, 0.2)">
                  <Activity className="w-12 h-12 text-primary mb-4 drop-shadow-[0_0_10px_rgba(0,255,136,0.8)]" />
                  <h3 className="text-2xl font-syne font-bold mb-2">24/7 Live Monitoring</h3>
                  <p className="text-gray-400 text-sm">Enable continuous observation of your smart contract state and get alerted of malicious activities.</p>
                </SpotlightCard>
              </motion.div>
            </motion.div>
          </div>
        </main>
      </div>
    </div>
  );
};
