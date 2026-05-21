import { useEffect, useRef, useState } from 'react'

export default function HowItWorks() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [activeIndex, setActiveIndex] = useState(0)

  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      // Total scrollable height is 200vh over 3 panels (300vh total).
      // Let's divide based on window scroll passing the sticky containers.
      const scrollPos = -rect.top
      const windowH = window.innerHeight

      let index = Math.floor(scrollPos / windowH)
      if (index < 0) index = 0
      if (index > 2) index = 2

      setActiveIndex(index)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <section className="relative w-full h-[300vh] bg-void" ref={containerRef}>
      {/* Panel 1 */}
      <div
        className={`sticky top-0 h-screen w-full flex items-center justify-center p-4 lg:p-16 transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] ${
          activeIndex > 0 ? 'scale-[0.92] blur-[8px] opacity-40' : 'scale-100 blur-0 opacity-100'
        }`}
      >
        <div className="bg-surface border border-border rounded-[24px] w-full max-w-[1200px] h-full max-h-[700px] p-10 lg:p-20 flex flex-col lg:flex-row items-center relative overflow-hidden">
          <span className="absolute left-[-20px] top-1/2 -translate-y-1/2 font-syne font-bold text-[180px] text-white opacity-[0.03] select-none pointer-events-none">
            01
          </span>

          <div className="flex-1 z-10">
            <h2 className="font-syne text-[40px] text-white mb-6">Upload & Parse</h2>
            <p className="font-mono text-[15px] text-ghost max-w-[400px] leading-[1.7]">
              We start by translating TEAL opcodes or Pythonic PyTeal down to its core abstract syntax tree. It's the first step to
              unpacking the logic of your contract.
            </p>
          </div>

          <div className="flex-1 flex justify-center items-center h-full relative z-10">
            <svg viewBox="0 0 280 280" className="w-[280px] h-[280px] opacity-80">
              <path
                d="M40,140 C40,40 240,240 240,140 C240,40 40,240 40,140"
                fill="none"
                stroke="#00C9A7"
                strokeWidth="2"
                strokeDasharray="600"
                className="animate-dash-offset"
              />
              <path
                d="M240,140 C240,40 40,240 40,140 C40,40 240,240 240,140"
                fill="none"
                stroke="#8BA3AD"
                strokeWidth="2"
                strokeDasharray="600"
                className="animate-dash-offset"
              />
              <circle cx="140" cy="140" r="4" fill="#00C9A7" className="animate-pulse-live" />
            </svg>
          </div>
        </div>
      </div>

      {/* Panel 2 */}
      <div
        className={`sticky top-0 h-screen w-full flex items-center justify-center p-4 lg:p-16 transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] ${
          activeIndex > 1
            ? 'scale-[0.92] blur-[8px] opacity-40'
            : activeIndex < 1
              ? 'opacity-0 scale-105 pointer-events-none'
              : 'scale-100 blur-0 opacity-100'
        }`}
      >
        <div className="bg-surface border border-border rounded-[24px] w-full max-w-[1200px] h-full max-h-[700px] p-10 lg:p-20 flex flex-col lg:flex-row items-center relative overflow-hidden">
          <span className="absolute left-[-20px] top-1/2 -translate-y-1/2 font-syne font-bold text-[180px] text-white opacity-[0.03] select-none pointer-events-none">
            02
          </span>

          <div className="flex-1 z-10">
            <h2 className="font-syne text-[40px] text-white mb-6">AI Scan & Score</h2>
            <p className="font-mono text-[15px] text-ghost max-w-[400px] leading-[1.7]">
              Every path is simulated. Our LLM + static analysis hybrid identifies known threat vectors, evaluates logic bounds, and scores
              every risk dimension from 0-100.
            </p>
          </div>

          <div className="flex-1 flex justify-center items-center h-full relative z-10">
            <div className="grid grid-cols-6 gap-2 relative p-4 group">
              <div className="absolute top-0 bottom-0 left-0 right-0 z-20 pointer-events-none overflow-hidden">
                <div className="w-full h-[2px] bg-teal shadow-[0_0_15px_rgba(0,201,167,0.9)] animate-[scanLine_1.5s_linear_infinite]" />
              </div>
              {Array.from({ length: 36 }).map((_, i) => (
                <div
                  key={i}
                  className={`w-8 h-8 md:w-10 md:h-10 border border-[rgba(0,201,167,0.2)] rounded-sm transition-all duration-1000 ${
                    i === 14 || i === 22 ? 'bg-amber border-amber/50 shadow-[0_0_8px_rgba(245,158,11,0.5)]' : 'bg-transparent'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Panel 3 */}
      <div
        className={`sticky top-0 h-screen w-full flex items-center justify-center p-4 lg:p-16 transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] ${
          activeIndex < 2 ? 'opacity-0 scale-105 pointer-events-none' : 'scale-100 blur-0 opacity-100'
        }`}
      >
        <div className="bg-surface border border-border rounded-[24px] w-full max-w-[1200px] h-full max-h-[700px] p-10 lg:p-20 flex flex-col lg:flex-row items-center relative overflow-hidden">
          <span className="absolute left-[-20px] top-1/2 -translate-y-1/2 font-syne font-bold text-[180px] text-white opacity-[0.03] select-none pointer-events-none">
            03
          </span>

          <div className="flex-1 z-10">
            <h2 className="font-syne text-[40px] text-white mb-6">Monitor & Certify</h2>
            <p className="font-mono text-[15px] text-ghost max-w-[400px] leading-[1.7]">
              Deploy to testnet and let the stream analysis verify your app's liveness and integrity. Once approved, an immutable NFT
              certificate drops on your address.
            </p>
          </div>

          <div className="flex-1 flex justify-center items-center h-full relative z-10 flex-col">
            <div className="w-[300px] h-[120px] relative mt-10">
              <svg viewBox="0 0 280 120" className="w-full h-full overflow-visible">
                <path
                  d="M 0 60 L 80 60 L 100 20 L 120 100 L 140 60 L 280 60"
                  fill="none"
                  stroke="#00C9A7"
                  strokeWidth="2"
                  strokeDasharray="300"
                  className="animate-[dashOffset_2s_ease_infinite]"
                  filter="drop-shadow(0 0 4px rgba(0,201,167,0.8))"
                />
              </svg>
            </div>
            <div className="mt-4 font-mono text-[11px] text-teal tracking-widest animate-pulse-live flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-teal" />
              CONTRACT ALIVE
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
