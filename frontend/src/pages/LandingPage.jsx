import { useEffect, useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import Navbar from "../components/landing/Navbar";
import Hero from "../components/landing/Hero";
import ProblemAgitation from "../components/landing/ProblemAgitation";
import StatsSection from "../components/landing/StatsSection";
import Features from "../components/landing/Features";
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
    <div className="min-h-screen bg-[#0a0e27]">
      <Helmet>
        <link rel="canonical" href="https://getmyplan.in" />
        <meta name="description" content="GetMyPlan is AI demand planning for fashion retail. Predict what you'll sell, where, and when with 92.7% forecast accuracy. 15-minute setup. 7-day free trial." />
        <meta property="og:title" content="GetMyPlan — AI-Powered Demand Planning for Fashion Retail" />
        <meta property="og:description" content="AI demand planning platform for fashion retailers. 92.7% forecast accuracy, 41% stockout reduction, 15-min setup." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://getmyplan.in" />
        <script type="application/ld+json">{JSON.stringify({
          "@context": "https://schema.org", "@type": "SoftwareApplication",
          "name": "GetMyPlan",
          "description": "AI-powered demand planning platform for fashion retailers. Predict demand with 92.7% accuracy, prevent stockouts, and optimize inventory across stores and channels.",
          "applicationCategory": "BusinessApplication", "operatingSystem": "Web",
          "offers": { "@type": "AggregateOffer", "priceCurrency": "USD", "lowPrice": "350", "highPrice": "1500", "offerCount": "4" },
          "aggregateRating": { "@type": "AggregateRating", "ratingValue": "4.9", "reviewCount": "200" }
        })}</script>
      </Helmet>
      <Navbar />
      <Hero onWatchDemo={openTour} onRequestDemo={openDemo} />
      <Testimonials />
      <StatsSection />
      <ProblemAgitation />
      <Features />
      <Pricing />
      <FAQ />
      <CTASection />
      <Footer />
      <ProductTour isOpen={showTour} onClose={closeTour} />
      <ContactModal isOpen={showDemo} onClose={() => setShowDemo(false)} />
    </div>
  );
}
