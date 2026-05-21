/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}', './index.html'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a',
        'dark-green': '#0d1f0d',
        primary: '#00ff88',
        secondary: '#00d4ff',
        danger: '#ff3333',
        warning: '#ffaa00',
        safe: '#00ff88',
        surface: 'rgba(255, 255, 255, 0.05)',
        'surface-hover': 'rgba(255, 255, 255, 0.1)',
        border: 'rgba(255, 255, 255, 0.1)',
        'border-glow': 'rgba(0, 255, 136, 0.5)',
      },
      fontFamily: {
        syne: ['Syne', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['"DM Sans"', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      animation: {
        'orbit-s': 'orbit 10s linear infinite',
        'orbit-f': 'orbit 2s linear infinite',
        'pulse-live': 'livePulse 2s infinite',
        'shimmer': 'shimmer 2s infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
      },
      keyframes: {
        orbit: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        livePulse: {
          '0%, 100%': { transform: 'scale(1)', boxShadow: '0 0 0 0 rgba(0,255,136,0.5)' },
          '50%': { transform: 'scale(1.2)', boxShadow: '0 0 0 6px rgba(0,255,136,0)' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: 1, textShadow: '0 0 10px rgba(0,255,136,0.5)' },
          '50%': { opacity: 0.7, textShadow: '0 0 20px rgba(0,255,136,0.8)' },
        }
      },
    },
  },
  plugins: [],
}
