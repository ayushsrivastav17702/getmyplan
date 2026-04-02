import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, NavLink, useLocation } from "react-router-dom";
import axios from "axios";
import { 
  Home, Upload, Settings, BarChart3, PieChart, TrendingUp, 
  MessageSquare, Menu, X, ChevronRight, Check, AlertCircle, Warehouse, Server, Award, XCircle, ShoppingCart, Clock, Layout as LayoutIcon
} from "lucide-react";

// Pages
import GettingStarted from "./pages/GettingStarted";
import DataUpload from "./pages/DataUpload";
import Configuration from "./pages/Configuration";
import CoreLogics from "./pages/CoreLogics";
import GapAnalysis from "./pages/GapAnalysis";
import BIDashboards from "./pages/BIDashboards";
import FAQChatbot from "./pages/FAQChatbot";
import WarehouseAnalysis from "./pages/WarehouseAnalysis";
import SFTPMonitor from "./pages/SFTPMonitor";
import DataQuality from "./pages/DataQuality";
import StockOutAnalysis from "./pages/StockOutAnalysis";
import ReplenishmentPlanner from "./pages/ReplenishmentPlanner";
import DOHAnalysis from "./pages/DOHAnalysis";
import PlanogramFillRate from "./pages/PlanogramFillRate";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Navigation items
const navItems = [
  { path: "/", label: "Getting Started", icon: Home },
  { path: "/upload", label: "Data Upload", icon: Upload },
  { path: "/config", label: "Configuration", icon: Settings },
  { path: "/core-logics", label: "Core Logics", icon: BarChart3 },
  { path: "/gap-analysis", label: "Gap Analysis", icon: PieChart },
  { path: "/stock-out", label: "Stock-Out Analysis", icon: XCircle },
  { path: "/replenishment", label: "Replenishment Planner", icon: ShoppingCart },
  { path: "/doh", label: "DOH Analysis", icon: Clock },
  { path: "/planogram", label: "Planogram Fill Rate", icon: LayoutIcon },
  { path: "/bi-dashboards", label: "BI Dashboards", icon: TrendingUp },
  { path: "/warehouse", label: "Warehouse", icon: Warehouse },
  { path: "/sftp-monitor", label: "SFTP Monitor", icon: Server },
  { path: "/data-quality", label: "Data Quality", icon: Award },
  { path: "/chatbot", label: "FAQ Chatbot", icon: MessageSquare },
];

// Sidebar Component
const Sidebar = ({ uploadStatus, isOpen, setIsOpen }) => {
  const location = useLocation();
  
  const getUploadCount = () => {
    if (!uploadStatus) return { uploaded: 0, total: 7 };
    const uploaded = Object.values(uploadStatus).filter(s => s.uploaded && s.valid).length;
    return { uploaded, total: 7 };
  };
  
  const { uploaded, total } = getUploadCount();
  const allUploaded = uploaded === total;

  return (
    <>
      {/* Mobile menu button */}
      <button
        data-testid="mobile-menu-toggle"
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white border border-slate-200 rounded shadow-sm"
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-40
        w-64 bg-white border-r border-slate-200 
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-200 bg-[#0176D3]">
          <h1 className="text-xl font-semibold tracking-tight text-white">
            Increff Analytics
          </h1>
        </div>

        {/* Upload Status */}
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Upload Status
            </span>
            <span className={`text-xs font-bold ${allUploaded ? 'text-green-600' : 'text-amber-600'}`}>
              {uploaded}/{total}
            </span>
          </div>
          <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 rounded-full ${allUploaded ? 'bg-green-500' : 'bg-[#0176D3]'}`}
              style={{ width: `${(uploaded / total) * 100}%` }}
            />
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <NavLink
                key={item.path}
                to={item.path}
                data-testid={`nav-${item.path.replace('/', '') || 'home'}`}
                onClick={() => setIsOpen(false)}
                className={`
                  flex items-center gap-3 px-4 py-2.5 text-sm rounded transition-all duration-200
                  ${isActive 
                    ? 'bg-[#0176D3] text-white shadow-sm' 
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}
                `}
              >
                <Icon size={18} strokeWidth={1.5} />
                <span className="font-medium">{item.label}</span>
                {isActive && <ChevronRight size={16} className="ml-auto" />}
              </NavLink>
            );
          })}
        </nav>

        {/* File Status List */}
        <div className="px-6 py-4 border-t border-slate-100 mt-auto">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 block">
            Data Files
          </span>
          <div className="space-y-2">
            {['style_master', 'sku_ean_master', 'store_master', 'warehouse_master', 'daily_sales', 'store_inventory', 'warehouse_inventory'].map((file) => {
              const status = uploadStatus?.[file];
              const isUploaded = status?.uploaded && status?.valid;
              
              return (
                <div key={file} className="flex items-center gap-2 text-xs">
                  {isUploaded ? (
                    <Check size={12} className="text-green-500" />
                  ) : (
                    <AlertCircle size={12} className="text-slate-300" />
                  )}
                  <span className={isUploaded ? 'text-slate-700' : 'text-slate-400'}>
                    {file.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/20 z-30"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

function App() {
  const [uploadStatus, setUploadStatus] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fetchUploadStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/upload/status`);
      setUploadStatus(response.data);
    } catch (error) {
      console.error("Error fetching upload status:", error);
    }
  }, []);

  useEffect(() => {
    fetchUploadStatus();
  }, [fetchUploadStatus]);

  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-[#F8F9FA]">
        <Sidebar 
          uploadStatus={uploadStatus} 
          isOpen={sidebarOpen}
          setIsOpen={setSidebarOpen}
        />
        
        <main className="flex-1 min-h-screen">
          <div className="mx-auto w-full max-w-[1600px] px-6 lg:px-10 py-8">
            <Routes>
              <Route path="/" element={<GettingStarted uploadStatus={uploadStatus} />} />
              <Route path="/upload" element={<DataUpload onUploadComplete={fetchUploadStatus} />} />
              <Route path="/config" element={<Configuration />} />
              <Route path="/core-logics" element={<CoreLogics />} />
              <Route path="/gap-analysis" element={<GapAnalysis />} />
              <Route path="/stock-out" element={<StockOutAnalysis />} />
              <Route path="/replenishment" element={<ReplenishmentPlanner />} />
              <Route path="/doh" element={<DOHAnalysis />} />
              <Route path="/planogram" element={<PlanogramFillRate />} />
              <Route path="/bi-dashboards" element={<BIDashboards />} />
              <Route path="/warehouse" element={<WarehouseAnalysis />} />
              <Route path="/sftp-monitor" element={<SFTPMonitor />} />
              <Route path="/data-quality" element={<DataQuality />} />
              <Route path="/chatbot" element={<FAQChatbot />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
