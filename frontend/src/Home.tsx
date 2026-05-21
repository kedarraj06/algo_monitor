import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Features from './components/Features'
import Philosophy from './components/Philosophy'
import ProtocolStack from './components/ProtocolStack'
import Pricing from './components/Pricing'
import Footer from './components/Footer'

export default function Home() {
  return (
    <div className="min-h-screen bg-void w-full relative">
      {/* Global Background UI Layers */}
      <div className="noise-layer" />
      
      <Navbar />
      <Hero />
      <Features />
      <Philosophy />
      <ProtocolStack />
      <Pricing />
      <Footer />
    </div>
  )
}
