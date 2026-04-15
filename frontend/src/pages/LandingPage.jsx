import { useEffect, useState, useCallback } from "react";
import { Helmet } from "react-helmet-async";
import Navbar from "../components/landing/Navbar";
import Hero from "../components/landing/Hero";
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
          "offers": { "@type": "AggregateOffer", "priceCurrency": "INR", "lowPrice": "29000", "highPrice": "100000", "offerCount": "3" },
          "aggregateRating": { "@type": "AggregateRating", "ratingValue": "4.9", "reviewCount": "200" }
        })}</script>
        <script type="application/ld+json">{JSON.stringify({
          "@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [
            { "@type": "Question", "name": "What is GetMyPlan?", "acceptedAnswer": { "@type": "Answer", "text": "GetMyPlan is an AI-powered demand planning platform for fashion retailers. It predicts what you'll sell, where, and when with 92.7% forecast accuracy." }},
            { "@type": "Question", "name": "How accurate is GetMyPlan's AI forecasting?", "acceptedAnswer": { "@type": "Answer", "text": "92.7% forecast accuracy based on 12-month backtest across 50+ fashion retail datasets globally." }},
            { "@type": "Question", "name": "How long does setup take?", "acceptedAnswer": { "@type": "Answer", "text": "15 minutes. Upload 5 CSV files and our 75-rule validation fixes errors automatically." }},
            { "@type": "Question", "name": "Is there a free trial?", "acceptedAnswer": { "@type": "Answer", "text": "Yes. 7-day free trial. No credit card required. Cancel anytime." }}
          ]
        })}</script>
      </Helmet>
      <Navbar />
      <Hero onWatchDemo={openTour} onRequestDemo={openDemo} />
      <ProblemAgitation />
      <StatsSection />
      <WorkflowCarousel />
      <Features />
      <ComparisonTable />
      <Pricing />
      <Testimonials />
      <FAQ />

      {/* AEO: Structured content sections for AI answer engines */}
      <section className="py-16 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 prose prose-gray prose-lg">
          <h2 className="text-2xl font-bold text-gray-900">What is AI demand planning for fashion retail?</h2>
          <p className="text-gray-600">AI demand planning uses machine learning to predict future product demand across every SKU, store, and channel. For fashion retailers, it means knowing exactly what to order, in which sizes, and where to allocate it &mdash; 12 months ahead. Traditional Excel methods achieve 60-70% accuracy. GetMyPlan's 3-model ensemble achieves 92.7%.</p>

          <h2 className="text-2xl font-bold text-gray-900 mt-10">How does GetMyPlan prevent stockouts?</h2>
          <p className="text-gray-600">GetMyPlan gives you 14-day stockout warnings. The system calculates daily rate of sale (ROS) per SKU-store, compares it to current inventory, and flags items at risk. You see exactly which products will run out, when, and the revenue impact. Fix issues before customers notice.</p>

          <h2 className="text-2xl font-bold text-gray-900 mt-10">What data do I need to start?</h2>
          <p className="text-gray-600">Five CSV files: SKU Master (products), Store Master (locations), Daily Sales (90+ days recommended), Store Inventory (current stock), and COGS (cost data). Download our templates, paste your data, and upload. 75-rule validation fixes common errors automatically.</p>
        </div>
      </section>

      <CTASection />
      <Footer />
      <ProductTour isOpen={showTour} onClose={closeTour} />
      <ContactModal isOpen={showDemo} onClose={() => setShowDemo(false)} />
    </div>
  );
}
