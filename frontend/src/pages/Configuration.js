import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Save, RotateCcw } from "lucide-react";

const Configuration = () => {
  const [config, setConfig] = useState({
    noos_enabled: true,
    ros_enabled: true,
    size_gap_enabled: true,
    lifecycle_enabled: true,
    start_date: "",
    end_date: "",
    min_shelf_life_days: 30,
    pivotal_size_threshold: 75,
    selected_seasons: [],
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await axios.get(`${API}/config`);
        setConfig(prev => ({ ...prev, ...response.data }));
      } catch (error) {
        console.error("Error fetching config:", error);
      }
    };
    fetchConfig();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.post(`${API}/config`, config);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      console.error("Error saving config:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setConfig({
      noos_enabled: true,
      ros_enabled: true,
      size_gap_enabled: true,
      lifecycle_enabled: true,
      start_date: "",
      end_date: "",
      min_shelf_life_days: 30,
      pivotal_size_threshold: 75,
      selected_seasons: [],
    });
  };

  const toggleModule = (module) => {
    setConfig(prev => ({ ...prev, [module]: !prev[module] }));
  };

  const modules = [
    { 
      key: "noos_enabled", 
      name: "NOOS Analysis", 
      description: "Never Out Of Stock - Identify core styles that should always be available" 
    },
    { 
      key: "ros_enabled", 
      name: "ROS Comparison", 
      description: "Rate of Sale - Compare healthy vs broken size set performance" 
    },
    { 
      key: "size_gap_enabled", 
      name: "Size Set Gap", 
      description: "Analyze size distribution and inventory balance" 
    },
    { 
      key: "lifecycle_enabled", 
      name: "Lifecycle Analysis", 
      description: "Track product lifecycle and seasonal patterns" 
    },
  ];

  return (
    <div className="animate-fade-in-up" data-testid="configuration-page">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-light tracking-tight text-neutral-900 mb-2">
            Configuration
          </h1>
          <p className="text-neutral-500">
            Configure analysis parameters and enable/disable modules
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            data-testid="reset-config-btn"
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-neutral-200 hover:border-neutral-400 transition-colors"
          >
            <RotateCcw size={16} />
            Reset
          </button>
          <button
            data-testid="save-config-btn"
            onClick={handleSave}
            disabled={saving}
            className={`flex items-center gap-2 px-6 py-2 text-sm font-medium transition-all ${
              saved 
                ? 'bg-emerald-500 text-white' 
                : 'bg-neutral-900 text-white hover:bg-neutral-800'
            }`}
          >
            {saving ? (
              <div className="spinner w-4 h-4 border-white" />
            ) : (
              <Save size={16} />
            )}
            {saved ? "Saved!" : "Save Configuration"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Analysis Modules */}
        <div className="bg-white border border-neutral-200 p-6">
          <h2 className="text-lg font-medium text-neutral-900 mb-6">
            Analysis Modules
          </h2>
          <div className="space-y-4">
            {modules.map((module) => (
              <div 
                key={module.key}
                data-testid={`module-toggle-${module.key}`}
                className={`p-4 border cursor-pointer transition-all ${
                  config[module.key] 
                    ? 'border-neutral-900 bg-neutral-50' 
                    : 'border-neutral-200 hover:border-neutral-300'
                }`}
                onClick={() => toggleModule(module.key)}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-neutral-900">{module.name}</h3>
                  <div className={`w-10 h-6 rounded-full p-1 transition-colors ${
                    config[module.key] ? 'bg-neutral-900' : 'bg-neutral-200'
                  }`}>
                    <div className={`w-4 h-4 bg-white rounded-full transition-transform ${
                      config[module.key] ? 'translate-x-4' : 'translate-x-0'
                    }`} />
                  </div>
                </div>
                <p className="text-sm text-neutral-500">{module.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Parameters */}
        <div className="space-y-6">
          {/* Date Range */}
          <div className="bg-white border border-neutral-200 p-6">
            <h2 className="text-lg font-medium text-neutral-900 mb-6">
              Analysis Period
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium uppercase tracking-widest text-neutral-400 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  data-testid="start-date-input"
                  value={config.start_date || ""}
                  onChange={(e) => setConfig(prev => ({ ...prev, start_date: e.target.value }))}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-xs font-medium uppercase tracking-widest text-neutral-400 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  data-testid="end-date-input"
                  value={config.end_date || ""}
                  onChange={(e) => setConfig(prev => ({ ...prev, end_date: e.target.value }))}
                  className="input"
                />
              </div>
            </div>
          </div>

          {/* Thresholds */}
          <div className="bg-white border border-neutral-200 p-6">
            <h2 className="text-lg font-medium text-neutral-900 mb-6">
              Analysis Thresholds
            </h2>
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-neutral-700">
                    Minimum Shelf Life (Days)
                  </label>
                  <span className="text-lg font-light text-neutral-900">
                    {config.min_shelf_life_days}
                  </span>
                </div>
                <input
                  type="range"
                  data-testid="shelf-life-slider"
                  min="7"
                  max="90"
                  value={config.min_shelf_life_days}
                  onChange={(e) => setConfig(prev => ({ ...prev, min_shelf_life_days: parseInt(e.target.value) }))}
                  className="w-full h-2 bg-neutral-200 appearance-none cursor-pointer accent-neutral-900"
                />
                <div className="flex justify-between text-xs text-neutral-400 mt-1">
                  <span>7 days</span>
                  <span>90 days</span>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-neutral-700">
                    Pivotal Size Threshold (%)
                  </label>
                  <span className="text-lg font-light text-neutral-900">
                    {config.pivotal_size_threshold}%
                  </span>
                </div>
                <input
                  type="range"
                  data-testid="pivotal-threshold-slider"
                  min="50"
                  max="100"
                  value={config.pivotal_size_threshold}
                  onChange={(e) => setConfig(prev => ({ ...prev, pivotal_size_threshold: parseInt(e.target.value) }))}
                  className="w-full h-2 bg-neutral-200 appearance-none cursor-pointer accent-neutral-900"
                />
                <div className="flex justify-between text-xs text-neutral-400 mt-1">
                  <span>50%</span>
                  <span>100%</span>
                </div>
                <p className="text-xs text-neutral-500 mt-2">
                  Styles with pivotal size availability above this threshold are classified as "healthy"
                </p>
              </div>
            </div>
          </div>

          {/* Calculation Reference */}
          <div className="bg-neutral-50 border border-neutral-200 p-6">
            <h3 className="text-sm font-medium text-neutral-700 mb-3">
              Calculation Reference
            </h3>
            <div className="text-xs text-neutral-500 space-y-2">
              <p><strong>ROS Formula:</strong> Total Quantity Sold ÷ Live Days</p>
              <p><strong>Sales Loss:</strong> (Healthy ROS × Broken Days) - Actual Broken Sales</p>
              <p><strong>Healthy Set:</strong> Pivotal size availability ≥ {config.pivotal_size_threshold}%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Configuration;
