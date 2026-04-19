/**
 * Auto-generate sitemap.xml from CMS content files + static route list.
 *
 * Runs as `yarn prebuild` before `craco build` and also callable manually:
 *   node scripts/generate-sitemap.js
 *
 * Reads slugs from:
 *   - src/data/productContent.js
 *   - src/data/solutionContent.js
 *   - src/data/industryContent.js
 *
 * Writes: public/sitemap.xml
 *
 * NOTE: Blog routes are kept in STATIC_ROUTES below and must stay in sync with
 * prerender.js's ROUTES array when new blog posts are added.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const BASE_URL = process.env.SITE_URL || 'https://getmyplan.in';
const TODAY = new Date().toISOString().slice(0, 10); // YYYY-MM-DD

// ─── Slug extraction ────────────────────────────────────────────────────────
// Parse top-level object keys from an ES module content file.
// Matches `  "some-slug": {` (indented keys, quoted, object value).
function extractSlugs(relativeFile) {
  const fullPath = path.join(ROOT, relativeFile);
  const src = fs.readFileSync(fullPath, 'utf-8');
  // Anchor to top-level: keys start at exactly 2 spaces of indent
  const re = /^ {2}"([a-z0-9-]+)":\s*\{/gm;
  const slugs = [];
  let m;
  while ((m = re.exec(src)) !== null) {
    slugs.push(m[1]);
  }
  if (slugs.length === 0) {
    throw new Error(`No slugs found in ${relativeFile}`);
  }
  return slugs;
}

// ─── Static routes ──────────────────────────────────────────────────────────
// Core marketing + legal + SEO landing + blog posts.
// Keep this list in sync with prerender.js ROUTES.
const STATIC_ROUTES = [
  { path: '/', priority: 1.0, changefreq: 'weekly' },
  { path: '/signup', priority: 0.8, changefreq: 'monthly' },
  { path: '/login', priority: 0.6, changefreq: 'monthly' },
  { path: '/products', priority: 0.9, changefreq: 'weekly' },
  { path: '/resources/api-reference', priority: 0.7, changefreq: 'monthly' },
  { path: '/vs/anaplan', priority: 0.8, changefreq: 'monthly' },
  { path: '/vs/blue-yonder', priority: 0.8, changefreq: 'monthly' },
  { path: '/ai-demand-planning', priority: 0.9, changefreq: 'monthly' },
  { path: '/privacy', priority: 0.3, changefreq: 'yearly' },
  { path: '/terms', priority: 0.3, changefreq: 'yearly' },
  { path: '/blog', priority: 0.9, changefreq: 'weekly' },
];

// Blog posts — keep aligned with prerender.js ROUTES.
const BLOG_SLUGS = [
  'best-demand-planning-software-india-2026',
  'reduce-stockouts-myntra-flipkart',
  'what-is-demand-forecasting-guide',
  'ai-demand-planning-vs-excel',
  'demand-planning-kpis-fashion-retail',
  'build-buy-plan-fashion-brand',
  'big-billion-days-bfcm-planning',
  'what-is-demand-sensing',
  'safety-stock-formula-calculate-optimize',
  'what-is-mape-forecast-accuracy',
  'ai-agents-supply-chain-2026',
  'generative-ai-demand-planning',
  'shopify-demand-planning-tools-2026',
  'improve-forecast-accuracy-methods',
  // Saudi
  'saudi-vision-2030-retail-demand-planning',
  'saudi-ecommerce-amazon-noon-namshi',
  'saudi-ramadan-planning-fashion',
  'saudi-logistics-port-delays-transportation',
  'saudi-consumer-behavior-modest-fashion',
  'saudi-multi-city-retail-planning',
  'saudi-ai-forecasting-vision-2030',
  // UAE
  'uae-demand-planning-fashion-ramadan-dss',
  'uae-multi-brand-namshi-ounass-retail',
  'uae-luxury-fashion-dubai-mall-planning',
  'uae-tourist-season-november-march-planning',
  'uae-vat-compliant-inventory-planning',
  'uae-supply-chain-jebel-ali-port-delays',
  'uae-fashion-consumer-behavior-modest-fashion',
  // South Africa
  'south-africa-demand-planning-fashion-2026',
  'south-africa-black-friday-strategy',
  'south-africa-multichannel-planning',
  'south-africa-supply-chain-load-shedding',
  'south-africa-consumer-behavior-local-brands',
  'south-africa-festive-season-planning',
  'south-africa-value-vs-premium',
  // USA
  'usa-demand-planning-fashion-2026',
  'usa-black-friday-cyber-monday-planning',
  'usa-regional-planning-northeast-southeast-west',
  'usa-d2c-shopify-planning',
  'usa-amazon-fashion-marketplace-planning',
  'usa-consumer-behavior-sustainability',
  'usa-supply-chain-tariffs-nearshoring',
];

// ─── XML building ───────────────────────────────────────────────────────────
function urlBlock(loc, priority, changefreq, lastmod) {
  return `  <url>
    <loc>${BASE_URL}${loc}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority.toFixed(1)}</priority>
  </url>`;
}

function buildSitemap() {
  const products = extractSlugs('src/data/productContent.js');
  const solutions = extractSlugs('src/data/solutionContent.js');
  const industries = extractSlugs('src/data/industryContent.js');

  const blocks = [];

  // Static routes
  for (const r of STATIC_ROUTES) {
    blocks.push(urlBlock(r.path, r.priority, r.changefreq, TODAY));
  }

  // Dynamic: Products
  blocks.push('\n  <!-- Products -->');
  for (const slug of products) {
    blocks.push(urlBlock(`/products/${slug}`, 0.8, 'monthly', TODAY));
  }

  // Dynamic: Solutions
  blocks.push('\n  <!-- Solutions -->');
  for (const slug of solutions) {
    blocks.push(urlBlock(`/solutions/${slug}`, 0.8, 'monthly', TODAY));
  }

  // Dynamic: Industries
  blocks.push('\n  <!-- Industries -->');
  for (const slug of industries) {
    blocks.push(urlBlock(`/industries/${slug}`, 0.8, 'monthly', TODAY));
  }

  // Blog posts
  blocks.push('\n  <!-- Blog Posts -->');
  for (const slug of BLOG_SLUGS) {
    blocks.push(urlBlock(`/blog/${slug}`, 0.8, 'monthly', TODAY));
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${blocks.join('\n')}
</urlset>
`;

  const outPath = path.join(ROOT, 'public', 'sitemap.xml');
  fs.writeFileSync(outPath, xml, 'utf-8');

  const total = STATIC_ROUTES.length + products.length + solutions.length + industries.length + BLOG_SLUGS.length;
  console.log(`✅ sitemap.xml generated → ${outPath}`);
  console.log(`   ${STATIC_ROUTES.length} static + ${products.length} products + ${solutions.length} solutions + ${industries.length} industries + ${BLOG_SLUGS.length} blog posts = ${total} URLs`);
  console.log(`   Base URL: ${BASE_URL}`);

  return { products, solutions, industries };
}

if (require.main === module) {
  buildSitemap();
}

module.exports = { buildSitemap, extractSlugs, STATIC_ROUTES, BLOG_SLUGS };
