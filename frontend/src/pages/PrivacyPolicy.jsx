import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Footer from "../components/landing/Footer";

export default function PrivacyPolicy() {
  return (
    <>
      <Helmet>
        <title>Privacy Policy - Getmyplan</title>
        <meta name="description" content="Getmyplan's privacy policy. Learn how we collect, use, and protect your data." />
      </Helmet>
      <div className="min-h-screen bg-white" data-testid="privacy-policy-page">
        <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition">
              <ArrowLeft className="h-4 w-4" /> Back to Home
            </Link>
            <img src="/getmyplan-logo-sm.png" alt="Getmyplan" className="h-7 w-auto ml-auto" />
          </div>
        </nav>

        <article className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
          <p className="text-sm text-gray-400 mb-10">Last updated: February 1, 2026</p>

          <div className="prose prose-gray max-w-none text-gray-700 space-y-8 text-[15px] leading-relaxed">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mt-0">1. Information We Collect</h2>
              <p>When you use Getmyplan, we collect information that you provide directly:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li><strong>Account Information:</strong> Name, email address, company name, and password when you create an account.</li>
                <li><strong>Business Data:</strong> Sales data, inventory data, SKU/EAN records, and store information that you upload for demand forecasting.</li>
                <li><strong>Usage Data:</strong> Pages visited, features used, time spent, and actions taken within the platform.</li>
                <li><strong>Device Data:</strong> Browser type, operating system, IP address, and device identifiers collected automatically.</li>
                <li><strong>Communication Data:</strong> Emails, support tickets, and feedback you send us.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">2. How We Use Your Information</h2>
              <p>We use the information collected to:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li>Provide, maintain, and improve our demand forecasting and inventory optimization services.</li>
                <li>Generate AI-powered forecasts, buy plans, and analytics based on your uploaded business data.</li>
                <li>Send transactional emails (account verification, password resets, billing notifications).</li>
                <li>Provide customer support and respond to your inquiries.</li>
                <li>Monitor and analyze usage patterns to improve the user experience.</li>
                <li>Detect, prevent, and address security incidents and technical issues.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">3. Data Storage & Security</h2>
              <p>Your data is stored in isolated, tenant-specific databases hosted on secure cloud infrastructure. We implement industry-standard security measures including:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li>Per-tenant database isolation (no shared data between organizations).</li>
                <li>Encryption in transit (TLS 1.3) and at rest (AES-256).</li>
                <li>Role-Based Access Control (RBAC) with 11 granular permission levels.</li>
                <li>Rate limiting, HSTS headers, CSP headers, and NoSQL injection prevention.</li>
                <li>Regular security audits and vulnerability assessments.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">4. Data Sharing & Third Parties</h2>
              <p>We do not sell, rent, or trade your personal information. We may share data with:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li><strong>Service Providers:</strong> Cloud hosting (MongoDB Atlas), email delivery, and analytics services that help us operate the platform.</li>
                <li><strong>AI Processing:</strong> Anonymized data may be processed by AI models (OpenAI) for the FAQ chatbot feature. No personally identifiable information is sent.</li>
                <li><strong>Legal Requirements:</strong> When required by law, court order, or to protect our rights.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">5. Your Rights</h2>
              <p>You have the right to:</p>
              <ul className="list-disc pl-6 space-y-1">
                <li><strong>Access:</strong> Request a copy of the personal data we hold about you.</li>
                <li><strong>Rectification:</strong> Request correction of inaccurate data.</li>
                <li><strong>Deletion:</strong> Request deletion of your account and associated data.</li>
                <li><strong>Export:</strong> Download your uploaded business data in standard formats.</li>
                <li><strong>Objection:</strong> Object to processing of your data for specific purposes.</li>
              </ul>
              <p>To exercise any of these rights, contact us at <a href="mailto:privacy@getmyplan.in" className="text-blue-600 hover:underline">privacy@getmyplan.in</a>.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">6. Cookies</h2>
              <p>We use essential cookies to maintain your session and authentication state. We do not use third-party advertising cookies. Analytics cookies may be used to understand usage patterns and improve the service.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">7. Data Retention</h2>
              <p>We retain your account data for as long as your account is active. Business data (sales, inventory) is retained for the duration of your subscription. Upon account deletion, all data is permanently removed within 30 days. Backups may retain data for up to 90 days before being purged.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">8. Changes to This Policy</h2>
              <p>We may update this privacy policy from time to time. We will notify you of material changes via email or a prominent notice on our platform. Continued use of Getmyplan after changes constitutes acceptance of the updated policy.</p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900">9. Contact Us</h2>
              <p>If you have questions about this privacy policy or our data practices, contact us at:</p>
              <ul className="list-none pl-0 space-y-1">
                <li>Email: <a href="mailto:privacy@getmyplan.in" className="text-blue-600 hover:underline">privacy@getmyplan.in</a></li>
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
