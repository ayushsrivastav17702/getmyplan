import { useEffect, useState, useCallback } from "react";
import Navbar from "../components/landing/Navbar";
import Hero from "../components/landing/Hero";
import TrustBar from "../components/landing/TrustBar";
import StatsSection from "../components/landing/StatsSection";
import Features from "../components/landing/Features";
import HowItWorks from "../components/landing/HowItWorks";
import ComparisonTable from "../components/landing/ComparisonTable";
import Pricing from "../components/landing/Pricing";
import Testimonials from "../components/landing/Testimonials";
import FAQ from "../components/landing/FAQ";
import CTASection from "../components/landing/CTASection";
import Footer from "../components/landing/Footer";
import ProductTour from "../components/landing/ProductTour";
import ContactModal from "../components/landing/ContactModal";

export default function LandingPage() {
  const [showTour, setShowTour] = useState(false);
  const [showDemo, setShowDemo] = useState(false);

  useEffect(() => { window.scrollTo(0, 0); }, []);

  const openTour = useCallback(() => setShowTour(true), []);
  const closeTour = useCallback(() => setShowTour(false), []);
  const openDemo = useCallback(() => setShowDemo(true), []);

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <Hero onWatchDemo={openTour} onRequestDemo={openDemo} />
      <TrustBar />
      <StatsSection />
      <Features />
      <HowItWorks />
      <ComparisonTable />
      <Pricing />
      <Testimonials />
      <FAQ />
      <CTASection />
      <Footer />
      <ProductTour isOpen={showTour} onClose={closeTour} />
      <ContactModal isOpen={showDemo} onClose={() => setShowDemo(false)} />
    </div>
  );
}
