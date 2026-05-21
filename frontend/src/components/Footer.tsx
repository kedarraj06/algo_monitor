export default function Footer() {
  return (
    <footer className="bg-[#040607] rounded-t-[48px] px-8 md:px-20 pt-20 pb-10 mt-[120px] border-t border-border">
      <div className="max-w-[1200px] mx-auto">
        <div className="flex flex-wrap justify-between items-start gap-10 mb-16">
          {/* LEFT: Brand */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <span className="font-syne font-bold text-[22px] text-white">
                AlgoShield<span className="text-teal ml-1">AI</span>
              </span>
            </div>
            <p className="font-mono text-xs text-ghost max-w-[280px] leading-[1.7]">
              AI-powered smart contract security for the Algorand ecosystem. Built for developers who ship with confidence.
            </p>
          </div>

          {/* RIGHT: Status */}
          <div className="flex flex-col gap-2">
            <span className="font-mono text-[9px] text-ghost tracking-[0.15em] mb-2 uppercase">System Status</span>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
              <span className="font-mono text-[11px] text-ghost">All systems operational</span>
            </div>
            <a href="https://testnet.algoexplorer.io" className="font-mono text-[10px] text-teal underline opacity-60 hover:opacity-100 transition-opacity">
              algoshield.testnet.algoexplorer.io
            </a>
          </div>
        </div>

        {/* MIDDLE GRID */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-10 mb-20">
          <div>
             <h4 className="font-mono text-[10px] text-teal tracking-[0.12em] uppercase mb-4">Product</h4>
             <div className="flex flex-col gap-3">
                {['Scanner', 'Monitor', 'Certify', 'Pricing', 'Changelog'].map(link => (
                  <a key={link} href="#" className="font-mono text-[12px] text-ghost hover:text-white transition-colors">{link}</a>
                ))}
             </div>
          </div>
          <div>
             <h4 className="font-mono text-[10px] text-teal tracking-[0.12em] uppercase mb-4">Docs</h4>
             <div className="flex flex-col gap-3">
                {['Quick Start', 'PyTeal Guide', 'TEAL Spec', 'API Reference', 'AlgoKit Setup'].map(link => (
                  <a key={link} href="#" className="font-mono text-[12px] text-ghost hover:text-white transition-colors">{link}</a>
                ))}
             </div>
          </div>
          <div>
             <h4 className="font-mono text-[10px] text-teal tracking-[0.12em] uppercase mb-4">Community</h4>
             <div className="flex flex-col gap-3">
                {['GitHub', 'Discord', 'Twitter/X', 'Algorand Forum', 'Algo Bharat'].map(link => (
                  <a key={link} href="#" className="font-mono text-[12px] text-ghost hover:text-white transition-colors">{link}</a>
                ))}
             </div>
          </div>
          <div>
             <h4 className="font-mono text-[10px] text-teal tracking-[0.12em] uppercase mb-4">Legal</h4>
             <div className="flex flex-col gap-3">
                {['Privacy Policy', 'Terms of Use', 'Security', 'DPDP Compliance'].map(link => (
                  <a key={link} href="#" className="font-mono text-[12px] text-ghost hover:text-white transition-colors">{link}</a>
                ))}
             </div>
          </div>
        </div>

        {/* BOTTOM BAR */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-8 border-t border-border mt-10">
          <span className="font-mono text-[11px] text-ghost opacity-50">© 2025 AlgoShield AI. Built on Algorand.</span>
          <div className="font-mono text-[10px] text-ghost opacity-30">build: a3f8c21 · testnet · v0.1.0-prototype</div>
        </div>
      </div>
    </footer>
  )
}
