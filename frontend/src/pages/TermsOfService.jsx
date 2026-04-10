import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Footer from "../components/landing/Footer";

export default function TermsOfService() {
  return (
    <>
      <Helmet>
        <title>Terms of Service - Getmyplan</title>
        <meta name="description" content="Getmyplan terms of service. Read the terms governing your use of our AI demand forecasting platform." />
      </Helmet>
      <div className="min-h-screen bg-white" data-testid="terms-of-service-page">
        <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition">
              <ArrowLeft className="h-4 w-4" /> Back to Home
            </Link>
            <img src="/getmyplan-logo-sm.png" alt="Getmyplan" className="h-7 w-auto ml-auto" />
          </div>
        </nav>

        <article className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">Terms of Service</h1>
          <p className="text-sm text-gray-400 mb-10">Last updated: February 1, 2026</p>

          <div className="prose prose-gray max-w-none text-gray-700 space-y-8 text-[15px] leading-relaxed">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mt-0">1. Acceptance of Terms</h2>
              <p>By accessing or using Getmyplan ("the Service"), you agree to be bound by these Terms of Service. If you are using the Service on behalf of an organization, you represent that you have the authority to bind that organization to these terms. If you do not agree, do not use the Service.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">2. Description of Service</h2>
              <p>Getmyplan is a cloud-based AI demand forecasting and inventory optimization platform designed for fashion retailers and D2C brands. The Service includes:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li>AI-powered demand forecasting using multi-model ensemble machine learning.</li>
                <li>Inventory analytics including stock-out prediction, replenishment planning, and Days-on-Hand analysis.</li>
                <li>Data upload, configuration, and visualization dashboards.</li>
                <li>Multi-tenant workspace management with role-based access control.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">3. Account Registration</h2>
              <p>To use the Service, you must create an account by providing accurate and complete information. You are responsible for:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li>Maintaining the confidentiality of your account credentials.</li>
                <li>All activities that occur under your account.</li>
                <li>Notifying us immediately of any unauthorized access to your account.</li>
              </ul>
              <p>We reserve the right to suspend or terminate accounts that violate these terms.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">4. Free Trial & Billing</h2>
              <p>New accounts receive a 7-day free trial with full access to all features. After the trial period:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li>You must subscribe to a paid plan to continue using the Service.</li>
                <li>Subscription fees are billed monthly or annually in advance.</li>
                <li>All fees are non-refundable except as required by applicable law.</li>
                <li>We may change pricing with 30 days notice. Existing subscriptions will be honored until renewal.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">5. Your Data</h2>
              <p>You retain all rights to the data you upload to Getmyplan ("Your Data"). By uploading data, you grant us a limited license to process, analyze, and store it solely for the purpose of providing the Service. We will not:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li>Sell or share Your Data with third parties for their benefit.</li>
                <li>Use Your Data to train general-purpose AI models.</li>
                <li>Access Your Data except as necessary to provide the Service or as required by law.</li>
              </ul>
              <p>You are responsible for ensuring that you have the right to upload and process the data you provide.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">6. Acceptable Use</h2>
              <p>You agree not to:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li>Use the Service for any unlawful purpose or in violation of any applicable laws.</li>
                <li>Attempt to gain unauthorized access to the Service or other users' accounts.</li>
                <li>Reverse engineer, decompile, or disassemble any part of the Service.</li>
                <li>Upload malicious code, viruses, or data designed to disrupt the Service.</li>
                <li>Exceed reasonable usage limits or abuse API endpoints.</li>
                <li>Resell or redistribute the Service without our written consent.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">7. Intellectual Property</h2>
              <p>The Service, including its design, code, algorithms, and documentation, is the intellectual property of Getmyplan. You may not copy, modify, or create derivative works of the Service. The forecasts, analytics, and reports generated from Your Data are yours to use freely.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">8. Service Availability & SLA</h2>
              <p>We strive for 99.9% uptime but do not guarantee uninterrupted access. The Service may be temporarily unavailable for maintenance, updates, or due to circumstances beyond our control. We will provide reasonable notice for planned maintenance when possible.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">9. Limitation of Liability</h2>
              <p>To the maximum extent permitted by law, Getmyplan shall not be liable for any indirect, incidental, consequential, or punitive damages arising from your use of the Service. Our total liability shall not exceed the amount paid by you in the 12 months preceding the claim. The Service provides forecasts and recommendations based on statistical models; business decisions made using these outputs are your sole responsibility.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">10. Termination</h2>
              <p>Either party may terminate this agreement at any time. Upon termination:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li>Your access to the Service will be revoked.</li>
                <li>You may export Your Data within 30 days of termination.</li>
                <li>After 30 days, all Your Data will be permanently deleted.</li>
              </ul>
              <p>We may terminate or suspend your account immediately for violation of these terms.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">11. Governing Law</h2>
              <p>These terms are governed by the laws of India. Any disputes shall be subject to the exclusive jurisdiction of the courts of Mumbai, India.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">12. Changes to Terms</h2>
              <p>We may update these terms from time to time. Material changes will be communicated via email or a prominent notice on the Service at least 30 days before they take effect. Continued use after changes constitutes acceptance.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">13. Contact</h2>
              <p>For questions about these terms, contact us at:</p>
              <ul className="list-none pl-0 space-y-1">
                <li>Email: <a href="mailto:legal@getmyplan.in" className="text-blue-600 hover:underline">legal@getmyplan.in</a></li>
                <li>Address: Mumbai, India</li>
              </ul>
            </section>
          </div>
        </article>

        <Footer />
      </div>
    </>
  );
}
