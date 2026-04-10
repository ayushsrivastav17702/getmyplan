import { Helmet } from "react-helmet-async";

const GLOBAL_SCHEMA = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Getmyplan",
  alternateName: "GetMyPlan",
  url: "https://getmyplan.in",
  logo: "https://getmyplan.in/logo.png",
  image: "https://getmyplan.in/og-image.jpg",
  description: "AI-powered demand forecasting, inventory optimization, and buy plan generation for fashion retailers and D2C brands.",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  offers: {
    "@type": "Offer",
    price: "30000",
    priceCurrency: "INR",
    priceValidUntil: "2026-12-31",
    availability: "https://schema.org/OnlineOnly",
    eligibleRegion: { "@type": "Country", name: "IN" },
  },
  aggregateRating: {
    "@type": "AggregateRating",
    ratingValue: "4.9",
    ratingCount: "127",
    bestRating: "5",
    worstRating: "1",
  },
  review: {
    "@type": "Review",
    reviewRating: { "@type": "Rating", ratingValue: "4.9", bestRating: "5" },
    author: { "@type": "Person", name: "Rahul Sharma" },
    reviewBody: "GetMyPlan reduced our stockouts by 40% and increased revenue by 25% in just 3 months.",
  },
  featureList: [
    "AI Demand Forecasting (3-model ensemble)",
    "Buy Plan Generator",
    "Stock-Out Prediction",
    "Inventory Optimization",
    "Executive Dashboard",
    "Multi-Channel Analytics",
    "Automated Replenishment",
    "Role-Based Access Control",
  ],
  sameAs: [
    "https://twitter.com/getmyplan",
    "https://linkedin.com/company/getmyplan",
  ],
};

const WEBSITE_SCHEMA = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  url: "https://getmyplan.in",
  name: "Getmyplan",
  description: "AI-powered demand planning and inventory optimization for fashion retailers",
  potentialAction: {
    "@type": "SearchAction",
    target: {
      "@type": "EntryPoint",
      urlTemplate: "https://getmyplan.in/search?q={search_term_string}",
    },
    "query-input": "required name=search_term_string",
  },
};

const PRICING_SCHEMA = {
  "@context": "https://schema.org",
  "@type": "Product",
  name: "Getmyplan Professional Plan",
  description: "AI demand forecasting and buy plan generation for multi-channel retailers",
  brand: { "@type": "Brand", name: "Getmyplan" },
  offers: [
    { "@type": "Offer", name: "Starter Plan", price: "30000", priceCurrency: "INR", description: "Up to 10 stores, 3 users, basic analytics" },
    { "@type": "Offer", name: "Professional Plan", price: "50000", priceCurrency: "INR", description: "Up to 50 stores, 10 users, AI forecasting, API access" },
    { "@type": "Offer", name: "Enterprise Plan", price: "100000", priceCurrency: "INR", description: "Unlimited stores, unlimited users, dedicated support" },
  ],
};

const FAQ_SCHEMA = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "How accurate is Getmyplan's demand forecasting?",
      acceptedAnswer: { "@type": "Answer", text: "Getmyplan uses a 3-model ensemble ML (Holt-Winters + Random Forest + Seasonal Decomposition) to achieve 91% forecast accuracy." },
    },
    {
      "@type": "Question",
      name: "How long does it take to get started?",
      acceptedAnswer: { "@type": "Answer", text: "From zero to insights in 15 minutes. Just upload your 7 CSV files and the AI analyzes immediately." },
    },
    {
      "@type": "Question",
      name: "Does Getmyplan integrate with my existing ERP?",
      acceptedAnswer: { "@type": "Answer", text: "Yes. Getmyplan supports CSV/Excel uploads, SFTP integration, and API access for custom integrations." },
    },
    {
      "@type": "Question",
      name: "Is there a free trial?",
      acceptedAnswer: { "@type": "Answer", text: "Yes. Getmyplan offers a 7-day free trial with no credit card required." },
    },
  ],
};

const BREADCRUMB_SCHEMA = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    { "@type": "ListItem", position: 1, name: "Home", item: "https://getmyplan.in" },
  ],
};

export const SEOSchemas = () => (
  <Helmet>
    <script type="application/ld+json">{JSON.stringify(GLOBAL_SCHEMA)}</script>
    <script type="application/ld+json">{JSON.stringify(WEBSITE_SCHEMA)}</script>
    <script type="application/ld+json">{JSON.stringify(PRICING_SCHEMA)}</script>
    <script type="application/ld+json">{JSON.stringify(FAQ_SCHEMA)}</script>
    <script type="application/ld+json">{JSON.stringify(BREADCRUMB_SCHEMA)}</script>
  </Helmet>
);
