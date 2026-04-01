import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { 
  Package, Store, Database, TrendingUp, Calendar,
  ArrowRight, CheckCircle, AlertCircle
} from "lucide-react";

const GettingStarted = ({ uploadStatus }) => {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const response = await axios.get(`${API}/analytics/overview`);
        setOverview(response.data);
      } catch (error) {
        console.error("Error fetching overview:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchOverview();
  }, []);

  const getUploadProgress = () => {
    if (!uploadStatus) return { uploaded: 0, total: 7 };
    const uploaded = Object.values(uploadStatus).filter(s => s.uploaded && s.valid).length;
    return { uploaded, total: 7 };
  };

  const { uploaded, total } = getUploadProgress();
  const allUploaded = uploaded === total;

  const metrics = [
    { label: "Total Styles", value: overview?.total_styles || 0, icon: Package, color: "#C4A47C" },
    { label: "Total Stores", value: overview?.total_stores || 0, icon: Store, color: "#18181B" },
    { label: "Total SKUs", value: overview?.total_skus || 0, icon: Database, color: "#52525B" },
    { label: "Sales Records", value: overview?.sales_records || 0, icon: TrendingUp, color: "#C4A47C" },
  ];

  const steps = [
    { step: 1, title: "Upload Data", description: "Upload your 7 required data files", done: uploaded >= 1 },
    { step: 2, title: "Configure Analysis", description: "Set parameters for analytics modules", done: false },
    { step: 3, title: "Run Analysis", description: "Generate gap analysis reports", done: false },
    { step: 4, title: "Review Insights", description: "Explore dashboards and recommendations", done: false },
  ];

  return (
    <div className="animate-fade-in-up" data-testid="getting-started-page">
      {/* Hero Section */}
      <div className="mb-12">
        <h1 className="text-4xl sm:text-5xl font-light tracking-tight text-neutral-900 mb-4">
          Fashion Retail<br />
          <span className="font-normal">Gap Analysis</span>
        </h1>
        <p className="text-lg text-neutral-500 max-w-2xl">
          Advanced analytics for inventory optimization & sales performance. 
          Identify revenue opportunities through rate-of-sale analysis.
        </p>
      </div>

      {/* Status Banner */}
      <div className={`p-6 mb-8 border ${allUploaded ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200'}`}>
        <div className="flex items-center gap-4">
          {allUploaded ? (
            <CheckCircle className="text-emerald-600" size={24} />
          ) : (
            <AlertCircle className="text-amber-600" size={24} />
          )}
          <div>
            <p className={`font-medium ${allUploaded ? 'text-emerald-900' : 'text-amber-900'}`}>
              {allUploaded 
                ? "All files uploaded! Ready for analysis." 
                : `${uploaded}/${total} files uploaded. Please upload remaining files.`}
            </p>
            <p className={`text-sm ${allUploaded ? 'text-emerald-700' : 'text-amber-700'}`}>
              {allUploaded 
                ? "Navigate to Configuration to set up your analysis parameters."
                : "Navigate to Data Upload to continue."}
            </p>
          </div>
          <a 
            href={allUploaded ? "/config" : "/upload"}
            data-testid="status-action-link"
            className="ml-auto flex items-center gap-2 px-4 py-2 bg-neutral-900 text-white text-sm font-medium hover:bg-neutral-800 transition-colors"
          >
            {allUploaded ? "Configure" : "Upload Files"}
            <ArrowRight size={16} />
          </a>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {metrics.map((metric, index) => {
          const Icon = metric.icon;
          return (
            <div 
              key={index}
              data-testid={`metric-${metric.label.toLowerCase().replace(' ', '-')}`}
              className="bg-white border border-neutral-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <span className="text-xs font-medium uppercase tracking-widest text-neutral-400">
                  {metric.label}
                </span>
                <Icon size={20} style={{ color: metric.color }} strokeWidth={1.5} />
              </div>
              <p className="text-4xl font-light tracking-tight text-neutral-900 metric-value">
                {loading ? "—" : metric.value.toLocaleString()}
              </p>
            </div>
          );
        })}
      </div>

      {/* Date Range */}
      {overview?.date_range?.start && (
        <div className="bg-white border border-neutral-200 p-6 mb-12">
          <div className="flex items-center gap-3 mb-2">
            <Calendar size={18} className="text-neutral-400" strokeWidth={1.5} />
            <span className="text-xs font-medium uppercase tracking-widest text-neutral-400">
              Data Date Range
            </span>
          </div>
          <p className="text-lg text-neutral-900">
            {new Date(overview.date_range.start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            <span className="mx-3 text-neutral-300">→</span>
            {new Date(overview.date_range.end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
          </p>
        </div>
      )}

      {/* Getting Started Steps */}
      <div className="mb-12">
        <h2 className="text-2xl font-normal tracking-tight text-neutral-900 mb-6">
          Getting Started
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {steps.map((item) => (
            <div 
              key={item.step}
              className={`p-6 border transition-all ${
                item.done 
                  ? 'bg-white border-emerald-200' 
                  : 'bg-white border-neutral-200'
              }`}
            >
              <div className="flex items-center gap-3 mb-3">
                <span className={`w-8 h-8 flex items-center justify-center text-sm font-medium ${
                  item.done 
                    ? 'bg-emerald-100 text-emerald-700' 
                    : 'bg-neutral-100 text-neutral-500'
                }`}>
                  {item.done ? <CheckCircle size={16} /> : item.step}
                </span>
                <h3 className="font-medium text-neutral-900">{item.title}</h3>
              </div>
              <p className="text-sm text-neutral-500">{item.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Analytics Modules Preview */}
      <div>
        <h2 className="text-2xl font-normal tracking-tight text-neutral-900 mb-6">
          Analytics Modules
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white border border-neutral-200 p-6">
            <h3 className="font-medium text-neutral-900 mb-2">NOOS Analysis</h3>
            <p className="text-sm text-neutral-500 mb-4">
              Identify Never Out Of Stock styles and availability gaps across stores.
            </p>
            <span className="text-xs font-medium uppercase tracking-widest text-[#C4A47C]">
              Availability Optimization
            </span>
          </div>
          <div className="bg-white border border-neutral-200 p-6">
            <h3 className="font-medium text-neutral-900 mb-2">ROS Comparison</h3>
            <p className="text-sm text-neutral-500 mb-4">
              Calculate Rate of Sale for broken vs healthy size sets to quantify loss.
            </p>
            <span className="text-xs font-medium uppercase tracking-widest text-[#C4A47C]">
              Sales Performance
            </span>
          </div>
          <div className="bg-white border border-neutral-200 p-6">
            <h3 className="font-medium text-neutral-900 mb-2">Size Set Gap</h3>
            <p className="text-sm text-neutral-500 mb-4">
              Optimize inventory distribution across sizes based on sales patterns.
            </p>
            <span className="text-xs font-medium uppercase tracking-widest text-[#C4A47C]">
              Inventory Balance
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GettingStarted;
