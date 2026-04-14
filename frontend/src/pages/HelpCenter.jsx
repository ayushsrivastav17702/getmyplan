import { useState } from "react";
import "./HelpCenter.css";
import {
  Search, BookOpen, ChevronRight, LogIn, Database, Upload,
  LayoutDashboard, AlertTriangle, Store, Brain, ShoppingCart,
  Settings, AlertCircle, Download, Headphones, MessageCircle,
  Mail, Phone,
} from "lucide-react";
import { Helmet } from "react-helmet-async";

const ARTICLES = [
  {
    id: 1, title: "How to Log In to GetMyPlan", category: "getting-started",
    categoryName: "Getting Started", icon: LogIn,
    description: "Learn how to log in to your GetMyPlan account and recover your password.",
    keywords: "login, sign in, password, forgot password, account access",
    content: `<h2>How to Log In to GetMyPlan</h2><p>This guide shows you how to log in to your GetMyPlan account.</p><h3>What You Need:</h3><ul><li>Your email address</li><li>Your password</li></ul><h3>Steps:</h3><ol><li>Open your web browser (Chrome or Safari)</li><li>Go to <strong>https://getmyplan.in/login</strong></li><li>You will see two boxes</li><li>Click the first box. Type your <strong>email address</strong></li><li>Click the second box. Type your <strong>password</strong></li><li>Click the blue <strong>"Log In"</strong> button</li><li>You are now inside GetMyPlan!</li></ol><h3>What If I Forgot My Password?</h3><ol><li>Click the small words <strong>"Forgot Password?"</strong> under the password box</li><li>Type your email</li><li>Check your email for a link</li><li>Click the link to make a new password</li></ol><div class="help-box"><strong>Still Stuck?</strong><br/>Click the chat button at the bottom right of your screen. We will help you right away.</div>`,
  },
  {
    id: 2, title: "How to Load Sample Data (See It Work in 30 Seconds)", category: "getting-started",
    categoryName: "Getting Started", icon: Database,
    description: "Load demo data to see what GetMyPlan looks like instantly.",
    keywords: "sample data, demo data, quick start, tutorial, onboarding",
    content: `<h2>How to Load Sample Data</h2><p>This guide shows you how to load fake data so you can see what GetMyPlan looks like.</p><h3>Why Do This First?</h3><ul><li>You will see charts and numbers right away</li><li>No need to upload your own files yet</li><li>Takes only 30 seconds</li></ul><h3>Steps:</h3><ol><li>Log in to GetMyPlan</li><li>On the left side, click <strong>"Data Upload"</strong></li><li>Look for a blue banner at the top that says <strong>"Load Sample Data"</strong></li><li>Click the <strong>"Load Sample Data"</strong> button</li><li>Wait 30 seconds</li><li>You will see a green message: <strong>"Sample data loaded!"</strong></li><li>Done! Now go to <strong>"Executive Dashboard"</strong> to see your charts</li></ol><div class="help-box"><strong>Still Stuck?</strong><br/>Click the chat button and type "Help with sample data"</div>`,
  },
  {
    id: 3, title: "How to Upload Your Own Data (Step-by-Step)", category: "data-upload",
    categoryName: "Data Upload", icon: Upload,
    description: "Upload your CSV files (SKU Master, Store Master, Daily Sales, Store Inventory, COGS).",
    keywords: "upload data, CSV upload, import data, file upload, data import",
    content: `<h2>How to Upload Your Own Data</h2><p>This guide shows you how to upload your own CSV files to GetMyPlan.</p><h3>What You Need:</h3><ul><li>5 CSV files (SKU Master, Store Master, Daily Sales, Store Inventory, COGS)</li><li>If you don't have them, ask us for templates</li></ul><h3>Steps:</h3><ol><li>Log in and click <strong>"Data Upload"</strong> on the left side</li><li>For each file type (SKU Master, Store Master, Daily Sales, Store Inventory, COGS):</li><li>Find the matching box, click <strong>"Upload"</strong>, select your CSV file</li><li>Wait for the green <strong>"Success"</strong> message</li></ol><h3>All Done!</h3><p>You should see <strong>5/5 files uploaded</strong> at the top. Now go to <strong>"Executive Dashboard"</strong> to see your real data.</p><div class="help-box warning"><strong>What If I Get an Error?</strong><br/>Read the red error message carefully. It tells you exactly what is wrong (example: "Missing column: product_name"). Fix your CSV file and try again. Or click chat and send us a screenshot.</div>`,
  },
  {
    id: 4, title: "How to Read the Executive Dashboard", category: "dashboard-guides",
    categoryName: "Dashboard Guides", icon: LayoutDashboard,
    description: "Understand what each number and chart means on your main dashboard.",
    keywords: "executive dashboard, KPI, revenue, margin, stock health, charts",
    content: `<h2>How to Read the Executive Dashboard</h2><p>This guide explains what each number on the main dashboard means.</p><h3>Where to Find It:</h3><ol><li>Log in to GetMyPlan</li><li>Click <strong>"Executive Dashboard"</strong> on the left side</li></ol><h3>The 4 Big Numbers at the Top:</h3><table><thead><tr><th>Number</th><th>What It Means</th><th>Good or Bad?</th></tr></thead><tbody><tr><td><strong>Revenue</strong></td><td>How much money you made</td><td>Higher is better</td></tr><tr><td><strong>Margin %</strong></td><td>How much profit you kept</td><td>Above 40% is good</td></tr><tr><td><strong>Units Sold</strong></td><td>How many items you sold</td><td>Higher is better</td></tr><tr><td><strong>Stock Health</strong></td><td>How healthy your inventory is</td><td>Above 75% is good</td></tr></tbody></table><h3>The Chart:</h3><p>Shows your revenue every day. Up is good. Down means you sold less that day.</p><div class="help-box"><strong>Still Confused?</strong><br/>Hover your mouse over any number. A small box will explain it.</div>`,
  },
  {
    id: 5, title: "How to Find Which Products Are About to Run Out", category: "dashboard-guides",
    categoryName: "Dashboard Guides", icon: AlertTriangle,
    description: "Identify products at risk of stockout before you lose sales.",
    keywords: "stockout, inventory alert, low stock, predictive, reorder",
    content: `<h2>How to Find Which Products Are About to Run Out</h2><p>This guide shows you how to see which products will run out of stock soon.</p><h3>Why This Matters:</h3><ul><li>Running out of stock = losing sales</li><li>This report shows you problems BEFORE they happen</li></ul><h3>Steps:</h3><ol><li>Log in to GetMyPlan</li><li>Click <strong>"Stock-Out Analysis"</strong> on the left side</li><li>Look at the <strong>"Total Stock-Outs"</strong> number</li><li>Click the <strong>"Predictive"</strong> tab at the top</li><li>You will see a list of products that will run out soon</li></ol><h3>What the Colors Mean:</h3><ul><li><strong>Critical</strong> = Will run out in less than 7 days. Order NOW.</li><li><strong>High</strong> = Will run out in 7-14 days. Order soon.</li><li><strong>Medium</strong> = Will run out in 14-30 days. Plan ahead.</li></ul><div class="help-box"><strong>Still Stuck?</strong><br/>Click chat and type "Help with stockout report"</div>`,
  },
  {
    id: 6, title: "How to See Which Stores Have Too Much or Too Little Stock", category: "dashboard-guides",
    categoryName: "Dashboard Guides", icon: Store,
    description: "Use the DOH Heatmap to identify overstocked and understocked stores.",
    keywords: "DOH, days on hand, heatmap, inventory health, overstock, understock",
    content: `<h2>How to See Which Stores Have Too Much or Too Little Stock</h2><p>This guide shows you how to use the DOH Heatmap.</p><h3>What is DOH?</h3><p>DOH = Days on Hand. It means: "How many days will your current stock last?"</p><h3>Steps:</h3><ol><li>Log in to GetMyPlan</li><li>Click <strong>"DOH Analysis"</strong> on the left side</li><li>You will see a big grid with colors</li></ol><h3>What the Colors Mean:</h3><ul><li><strong>Green</strong> = Perfect. You have the right amount.</li><li><strong>Yellow</strong> = Too much stock. You might have to discount later.</li><li><strong>Red</strong> = Too little stock. You might run out soon.</li><li><strong>Black</strong> = Out of stock right now. Lost sales!</li></ul><h3>How to Fix Red or Black:</h3><ol><li>Click on the red or black square</li><li>A box will open with details</li><li>Click the <strong>"Reorder"</strong> button</li><li>It will tell you exactly how many units to order</li></ol><div class="help-box"><strong>Quick Tip:</strong><br/>Look for stores with lots of red squares. They need attention first.</div>`,
  },
  {
    id: 7, title: "How to Generate an AI Forecast", category: "advanced-features",
    categoryName: "Advanced Features", icon: Brain,
    description: "Get 12-month demand predictions powered by AI.",
    keywords: "AI forecast, demand forecasting, machine learning, prediction, future demand",
    content: `<h2>How to Generate an AI Forecast</h2><p>This guide shows you how to see what will sell in the next 12 months.</p><h3>What You Need First:</h3><ul><li>At least 30 days of sales data uploaded</li><li>90+ days is better for accurate results</li></ul><h3>Steps:</h3><ol><li>Log in to GetMyPlan</li><li>Click <strong>"AI Demand Planning"</strong> on the left side</li><li>Click the blue <strong>"Generate AI Plan"</strong> button at the top right</li><li>Wait about 30-60 seconds</li><li>You will see a chart showing the next 12 months</li></ol><h3>Confidence Score:</h3><ul><li><strong>Above 90%</strong> = Very reliable. Trust this forecast.</li><li><strong>80-90%</strong> = Good. Use it for planning.</li><li><strong>Below 80%</strong> = Upload more sales history for better results.</li></ul><div class="help-box"><strong>What to Do With This:</strong><br/>Use the forecast to plan how much to buy. Go to "Replenishment Planner" to create purchase orders.</div>`,
  },
  {
    id: 8, title: "How to Create a Purchase Order", category: "advanced-features",
    categoryName: "Advanced Features", icon: ShoppingCart,
    description: "Generate purchase orders for products that need reordering.",
    keywords: "purchase order, PO, reorder, procurement, supplier order",
    content: `<h2>How to Create a Purchase Order</h2><p>This guide shows you how to create a purchase order (PO) for products you need to reorder.</p><h3>Steps:</h3><ol><li>Log in to GetMyPlan</li><li>Click <strong>"Replenishment Planner"</strong> on the left side</li><li>You will see a list of products that need to be reordered</li><li>Look at the <strong>"Order Qty"</strong> column</li><li>Click <strong>"Generate PO"</strong> at the top right</li><li>A file will download to your computer</li><li>Open the file. It is your Purchase Order</li><li>Send this file to your supplier</li></ol><h3>What's in the PO File:</h3><ul><li>Product names and how many to order</li><li>Which store needs them</li><li>Total cost</li></ul><div class="help-box"><strong>Quick Tip:</strong><br/>Review the quantities before sending to your supplier. You can edit the file in Excel if needed.</div>`,
  },
  {
    id: 9, title: "How to Change Your Settings", category: "account-settings",
    categoryName: "Account Settings", icon: Settings,
    description: "Configure GetMyPlan parameters to match your business.",
    keywords: "settings, configuration, PSA benchmark, ROS period, safety stock",
    content: `<h2>How to Change Your Settings</h2><p>This guide shows you how to change important settings in GetMyPlan.</p><h3>Steps:</h3><ol><li>Log in to GetMyPlan</li><li>Scroll down to <strong>"ADMIN"</strong> on the left side</li><li>Click <strong>"Configuration"</strong></li></ol><h3>Settings You Can Change:</h3><table><thead><tr><th>Setting</th><th>What It Does</th><th>Recommended</th></tr></thead><tbody><tr><td><strong>PSA Benchmark</strong></td><td>Target for Stock Health</td><td>75%</td></tr><tr><td><strong>ROS Period</strong></td><td>Days used to calculate sales rate</td><td>30 days</td></tr><tr><td><strong>Safety Stock Days</strong></td><td>Extra buffer to prevent stockouts</td><td>7 days</td></tr></tbody></table><h3>How to Change:</h3><ol><li>Move the slider or type a number</li><li>Click <strong>"Save"</strong></li><li>Changes happen immediately</li></ol><div class="help-box"><strong>What If I Mess Up?</strong><br/>Click "Reset to Defaults" to go back to the original settings.</div>`,
  },
  {
    id: 10, title: "What to Do If Something Is Not Working", category: "troubleshooting",
    categoryName: "Troubleshooting", icon: AlertCircle,
    description: "Solutions for common problems in GetMyPlan.",
    keywords: "troubleshooting, error, fix, problem, not working, bug",
    content: `<h2>What to Do If Something Is Not Working</h2><h3>Dashboard is empty or shows "Failed to load"</h3><ol><li>Refresh the page (press F5)</li><li>Wait 10 seconds</li><li>If still empty, wait 2 minutes and try again</li><li>If still not working, click chat and tell us</li></ol><h3>File upload gives an error</h3><ol><li>Read the red error message carefully</li><li>It tells you exactly what is wrong</li><li>Open your CSV in Excel, fix the issue, save and try again</li></ol><h3>Numbers look wrong</h3><ol><li>Check if you uploaded the correct date range</li><li>Click the date filter and select "Last 90 Days"</li></ol><h3>I forgot my password</h3><ol><li>Go to the login page</li><li>Click "Forgot Password?"</li><li>Check your email for a reset link</li></ol><div class="help-box"><strong>Nothing Worked?</strong><br/>Click the chat button at the bottom right. We reply in 5 minutes during business hours.</div>`,
  },
  {
    id: 11, title: "How to Export Reports (PDF or Excel)", category: "reporting",
    categoryName: "Reporting", icon: Download,
    description: "Download reports to share with your team or analyze in Excel.",
    keywords: "export, PDF, Excel, CSV, download, report, share",
    content: `<h2>How to Export Reports</h2><p>This guide shows you how to download reports.</p><h3>Steps:</h3><ol><li>Go to any dashboard</li><li>Look at the top right corner</li><li>Click <strong>"Export PDF"</strong> or <strong>"Export CSV"</strong></li><li>A file will download to your computer</li></ol><h3>What Reports Can I Export?</h3><ul><li>Executive Dashboard (KPIs and charts)</li><li>BI Dashboards (revenue trends, category mix)</li><li>DOH Analysis (inventory health)</li><li>Stock-Out Analysis (lost sales report)</li><li>Replenishment Planner (purchase orders)</li></ul><div class="help-box"><strong>Still Stuck?</strong><br/>Click chat and type "Help with export"</div>`,
  },
  {
    id: 12, title: "How to Get Help Fast", category: "support",
    categoryName: "Support", icon: Headphones,
    description: "All the ways to reach GetMyPlan support.",
    keywords: "support, help, contact, chat, WhatsApp, email, customer service",
    content: `<h2>How to Get Help Fast</h2><h3>Option 1: Live Chat (Fastest)</h3><ol><li>Look at the bottom right corner of any page</li><li>Click the chat bubble</li><li>Type your question</li><li>We reply in 5 minutes during business hours</li></ol><h3>Option 2: Email</h3><p>Send email to: <strong>support@getmyplan.in</strong></p><h3>Option 3: Knowledge Base (You Are Here)</h3><p>Browse these articles anytime. Use the search box to find what you need.</p><h3>Our Business Hours (IST):</h3><ul><li>Monday - Friday: 9:00 AM - 9:00 PM</li><li>Saturday: 10:00 AM - 6:00 PM</li><li>Sunday: Limited support (urgent only)</li></ul><div class="help-box success"><strong>We Are Here to Help!</strong><br/>No question is too small. We want you to succeed with GetMyPlan.</div>`,
  },
];

const CATEGORIES = [
  { id: "all", name: "All Articles", icon: BookOpen },
  { id: "getting-started", name: "Getting Started", icon: LogIn },
  { id: "data-upload", name: "Data Upload", icon: Upload },
  { id: "dashboard-guides", name: "Dashboard Guides", icon: LayoutDashboard },
  { id: "advanced-features", name: "Advanced Features", icon: Brain },
  { id: "account-settings", name: "Account Settings", icon: Settings },
  { id: "troubleshooting", name: "Troubleshooting", icon: AlertCircle },
  { id: "reporting", name: "Reporting", icon: Download },
  { id: "support", name: "Support", icon: Headphones },
];

const HelpCenter = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedArticle, setSelectedArticle] = useState(null);

  const filteredArticles = ARTICLES.filter((a) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch = !q || a.title.toLowerCase().includes(q) || a.keywords.toLowerCase().includes(q) || a.description.toLowerCase().includes(q);
    const matchesCat = selectedCategory === "all" || a.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  const getCategoryCount = (id) => (id === "all" ? ARTICLES.length : ARTICLES.filter((a) => a.category === id).length);

  if (selectedArticle) {
    return (
      <div className="help-article-page" data-testid="help-article">
        <Helmet>
          <title>{`${selectedArticle.title} - GetMyPlan Help Center`}</title>
          <meta name="description" content={selectedArticle.description} />
        </Helmet>
        <div className="help-article-header">
          <button data-testid="help-back-btn" className="help-back-btn" onClick={() => setSelectedArticle(null)}>
            &#8592; Back to Help Center
          </button>
          <span className="help-cat-badge">{selectedArticle.categoryName}</span>
          <h1 className="help-article-title">{selectedArticle.title}</h1>
          <p className="help-article-desc">{selectedArticle.description}</p>
        </div>
        <div className="help-article-body" dangerouslySetInnerHTML={{ __html: selectedArticle.content }} />
        <div className="help-article-footer">
          <h3>Still need help?</h3>
          <div className="help-support-row">
            <button onClick={() => window.Tawk_API?.maximize?.()}><MessageCircle size={18} /> Live Chat</button>
            <a href="mailto:support@getmyplan.in"><Mail size={18} /> Email Support</a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="help-center-page" data-testid="help-center">
      <Helmet>
        <title>Help Center - GetMyPlan</title>
        <meta name="description" content="Step-by-step guides for using GetMyPlan. Learn how to upload data, read dashboards, generate forecasts, and more." />
      </Helmet>
      <div className="help-hero">
        <h1>How can we help you?</h1>
        <p>Step-by-step guides to master GetMyPlan</p>
        <div className="help-search" data-testid="help-search">
          <Search size={20} />
          <input type="text" placeholder="Search for help... (e.g., 'upload data', 'stockout', 'forecast')" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
        </div>
      </div>
      <div className="help-layout">
        <aside className="help-sidebar">
          <h3>Categories</h3>
          <ul>
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              return (
                <li key={cat.id}>
                  <button data-testid={`help-cat-${cat.id}`} className={selectedCategory === cat.id ? "active" : ""} onClick={() => setSelectedCategory(cat.id)}>
                    <Icon size={16} />
                    <span>{cat.name}</span>
                    <span className="help-cat-count">{getCategoryCount(cat.id)}</span>
                  </button>
                </li>
              );
            })}
          </ul>
          <div className="help-sidebar-cta">
            <p>Need more help?</p>
            <button onClick={() => window.Tawk_API?.maximize?.()}><MessageCircle size={16} /> Chat with us</button>
          </div>
        </aside>
        <div className="help-articles">
          {filteredArticles.length === 0 ? (
            <div className="help-empty">
              <p>No articles found for &ldquo;{searchQuery}&rdquo;</p>
              <button onClick={() => { setSearchQuery(""); setSelectedCategory("all"); }}>Clear search</button>
            </div>
          ) : (
            <>
              <p className="help-count">{filteredArticles.length} article{filteredArticles.length !== 1 ? "s" : ""}</p>
              <div className="help-list">
                {filteredArticles.map((a) => {
                  const Icon = a.icon;
                  return (
                    <button key={a.id} data-testid={`help-article-${a.id}`} className="help-card" onClick={() => { setSelectedArticle(a); window.scrollTo({ top: 0, behavior: "smooth" }); }}>
                      <div className="help-card-icon"><Icon size={22} /></div>
                      <div className="help-card-body">
                        <span className="help-card-cat">{a.categoryName}</span>
                        <h3>{a.title}</h3>
                        <p>{a.description}</p>
                      </div>
                      <ChevronRight size={18} className="help-card-arrow" />
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default HelpCenter;
