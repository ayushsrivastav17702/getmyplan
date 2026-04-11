/**
 * Pre-render public routes to static HTML for SEO.
 * Runs after `craco build` — opens each route in headless Chrome,
 * captures the rendered DOM, and writes it back to build/.
 * 
 * React 19 compatible (framework-agnostic — just captures final HTML).
 */

const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
const path = require('path');

const BUILD_DIR = path.join(__dirname, 'build');
const PORT = 45678;

// All public routes to pre-render (landing + blogs + SEO + legal pages)
// Note: /blog index is last so the blog/ directory already exists from sub-routes
const ROUTES = [
  '/',
  '/login',
  '/register',
  '/privacy',
  '/terms',
  '/vs/anaplan',
  '/vs/blue-yonder',
  '/ai-demand-planning',
  '/blog/best-demand-planning-software-india-2026',
  '/blog/reduce-stockouts-myntra-flipkart',
  '/blog/what-is-demand-forecasting-guide',
  '/blog/ai-demand-planning-vs-excel',
  '/blog/demand-planning-kpis-fashion-retail',
  '/blog/build-buy-plan-fashion-brand',
  '/blog/big-billion-days-bfcm-planning',
  '/blog/what-is-demand-sensing',
  '/blog/safety-stock-formula-calculate-optimize',
  '/blog/what-is-mape-forecast-accuracy',
  '/blog/ai-agents-supply-chain-2026',
  '/blog/generative-ai-demand-planning',
  '/blog/shopify-demand-planning-tools-2026',
  '/blog/improve-forecast-accuracy-methods',
  '/blog/saudi-vision-2030-retail-demand-planning',
  '/blog/saudi-ecommerce-amazon-noon-namshi',
  '/blog/saudi-ramadan-planning-fashion',
  '/blog/saudi-logistics-port-delays-transportation',
  '/blog/saudi-consumer-behavior-modest-fashion',
  '/blog/saudi-multi-city-retail-planning',
  '/blog/saudi-ai-forecasting-vision-2030',
  '/blog/uae-demand-planning-fashion-ramadan-dss',
  '/blog/uae-multi-brand-namshi-ounass-retail',
  '/blog/uae-luxury-fashion-dubai-mall-planning',
  '/blog/uae-tourist-season-november-march-planning',
  '/blog/uae-vat-compliant-inventory-planning',
  '/blog/uae-supply-chain-jebel-ali-port-delays',
  '/blog/uae-fashion-consumer-behavior-modest-fashion',
  '/blog',
];

// Simple static file server for the build folder
function createServer() {
  const mimeTypes = {
    '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css',
    '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.xml': 'application/xml',
    '.txt': 'text/plain', '.woff': 'font/woff', '.woff2': 'font/woff2',
  };

  return http.createServer((req, res) => {
    let urlPath = req.url.split('?')[0];
    let filePath = path.join(BUILD_DIR, urlPath === '/' ? 'index.html' : urlPath);
    
    // If path is a directory, try index.html inside it
    if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
      filePath = path.join(filePath, 'index.html');
    }
    
    // SPA fallback: if file doesn't exist, serve root index.html
    if (!fs.existsSync(filePath)) {
      filePath = path.join(BUILD_DIR, 'index.html');
    }

    const ext = path.extname(filePath);
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    
    try {
      const content = fs.readFileSync(filePath);
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    } catch (e) {
      res.writeHead(404);
      res.end('Not found');
    }
  });
}

async function prerender() {
  console.log(`\n🔍 Pre-rendering ${ROUTES.length} public routes for SEO...\n`);
  
  const server = createServer();
  await new Promise(resolve => server.listen(PORT, resolve));

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  let success = 0;
  let failed = 0;

  for (const route of ROUTES) {
    try {
      const page = await browser.newPage();
      
      // Block unnecessary resources to speed up rendering
      await page.setRequestInterception(true);
      page.on('request', (req) => {
        const type = req.resourceType();
        if (['image', 'font', 'media'].includes(type)) {
          req.abort();
        } else {
          req.continue();
        }
      });

      await page.goto(`http://localhost:${PORT}${route}`, {
        waitUntil: 'networkidle0',
        timeout: 20000,
      });

      // Wait for React to finish rendering
      await page.waitForSelector('#root', { timeout: 10000 });
      await page.evaluate(() => new Promise(r => setTimeout(r, 500)));

      // Remove scripts that shouldn't be in pre-rendered HTML (like setInterval badge hider)
      // but keep React bundle scripts for hydration
      const html = await page.content();

      // Determine output path
      const outputDir = path.join(BUILD_DIR, route === '/' ? '' : route);
      const outputFile = route === '/' 
        ? path.join(BUILD_DIR, 'index.html') 
        : path.join(outputDir, 'index.html');

      // Create directory structure
      if (route !== '/') {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      fs.writeFileSync(outputFile, html, 'utf-8');
      success++;
      console.log(`  ✅ ${route}`);
      
      await page.close();
    } catch (err) {
      failed++;
      console.log(`  ❌ ${route} — ${err.message}`);
    }
  }

  await browser.close();
  server.close();

  console.log(`\n📊 Pre-rendering complete: ${success} succeeded, ${failed} failed out of ${ROUTES.length} routes.`);
  
  if (failed > 0) {
    console.log('⚠️  Failed routes will still work as normal SPA (client-side rendered).\n');
  } else {
    console.log('🎉 All routes pre-rendered successfully!\n');
  }
}

prerender().catch(err => {
  console.error('Pre-rendering failed:', err.message);
  console.log('Build will continue — SPA fallback still works.');
  process.exit(0); // Don't fail the build
});
