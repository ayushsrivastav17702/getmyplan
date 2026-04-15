import { useEffect, useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import Navbar from "../components/landing/Navbar";
import Hero from "../components/landing/Hero";
import TrustBar from "../components/landing/TrustBar";
import ProblemAgitation from "../components/landing/ProblemAgitation";
import StatsSection from "../components/landing/StatsSection";
import Features from "../components/landing/Features";
import WorkflowCarousel from "../components/landing/WorkflowCarousel";
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
      <Helmet>
        <link rel="canonical" href="https://getmyplan.in" />
        <meta property="og:title" content="GetMyPlan — AI-Powered Demand Planning for Fashion Retail" />
        <meta property="og:description" content="AI demand planning platform for fashion retailers. 92.7% forecast accuracy, 41% stockout reduction, 15-min setup." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://getmyplan.in" />
      </Helmet>
      <Navbar />
      <Hero onWatchDemo={openTour} onRequestDemo={openDemo} />
      <TrustBar />
      <ProblemAgitation />
      <StatsSection />
      <WorkflowCarousel />
      <Features />
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
