import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Clock } from 'lucide-react';

interface AlertProps {
  show: boolean;
  message: string;
  onClose?: () => void;
}

export const AlertBanner = ({ show, message, onClose }: AlertProps) => {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="fixed top-24 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-2xl px-4"
        >
          <div className="bg-danger/20 border border-danger shadow-[0_0_30px_rgba(255,51,51,0.5)] backdrop-blur-md rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="text-danger w-8 h-8 animate-pulse" />
              <div>
                <h3 className="text-danger font-bold font-syne text-lg">⚠️ Suspicious Activity Detected</h3>
                <p className="text-gray-200 text-sm">{message}</p>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
