import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Filter, ChevronDown, ChevronUp, X, Calendar } from "lucide-react";

const FilterPanel = ({ 
  filters, 
  filterOptions, 
  onFilterChange, 
  onApply, 
  onReset,
  pageType = "common" // "common", "gap-analysis", "core-logics"
}) => {
  const [isOpen, setIsOpen] = useState(false);

  // Count active filters
  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.startDate) count++;
    if (filters.endDate) count++;
    if (filters.categories?.length > 0) count++;
    if (filters.channels?.length > 0) count++;
    if (filters.regions?.length > 0) count++;
    if (pageType === "gap-analysis") {
      if (filters.understockThreshold !== undefined && filters.understockThreshold !== -100) count++;
      if (filters.overstockThreshold !== undefined && filters.overstockThreshold !== 100) count++;
    }
    if (pageType === "core-logics") {
      if (filters.minSize !== undefined && filters.minSize !== 0) count++;
      if (filters.minSizePercent !== undefined && filters.minSizePercent !== 0) count++;
    }
    return count;
  };

  const activeCount = getActiveFilterCount();

  const handleMultiSelect = (field, value) => {
    const current = filters[field] || [];
    const updated = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value];
    onFilterChange(field, updated);
  };

  return (
    <div className="mb-6">
      {/* Filter Trigger */}
      <button
        data-testid="filter-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-controls="filter-panel"
        className="filter-panel-trigger"
      >
        <div className="flex items-center gap-3">
          <Filter size={18} className="text-slate-500" />
          <span className="font-medium text-slate-700">Filters</span>
          {activeCount > 0 && (
            <span data-testid="active-filter-count" className="filter-badge">
              {activeCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {activeCount > 0 && (
            <span className="text-sm text-slate-500">
              {activeCount} filter{activeCount !== 1 ? 's' : ''} applied
            </span>
          )}
          {isOpen ? (
            <ChevronUp size={20} className="text-slate-400" />
          ) : (
            <ChevronDown size={20} className="text-slate-400" />
          )}
        </div>
      </button>

      {/* Filter Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            id="filter-panel"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="filter-panel">
              {/* Filter Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                {/* Date Range - Start */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 }}
                >
                  <label className="filter-label">
                    <Calendar size={12} className="inline mr-1" />
                    Start Date
                  </label>
                  <input
                    type="date"
                    data-testid="filter-start-date"
                    value={filters.startDate || ""}
                    onChange={(e) => onFilterChange("startDate", e.target.value)}
                    className="filter-input"
                  />
                </motion.div>

                {/* Date Range - End */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <label className="filter-label">
                    <Calendar size={12} className="inline mr-1" />
                    End Date
                  </label>
                  <input
                    type="date"
                    data-testid="filter-end-date"
                    value={filters.endDate || ""}
                    onChange={(e) => onFilterChange("endDate", e.target.value)}
                    className="filter-input"
                  />
                </motion.div>

                {/* Category */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 }}
                >
                  <label className="filter-label">Category</label>
                  <div className="relative">
                    <select
                      data-testid="filter-category"
                      multiple
                      value={filters.categories || []}
                      onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions, option => option.value);
                        onFilterChange("categories", selected);
                      }}
                      className="filter-select h-auto min-h-[40px] max-h-[120px]"
                    >
                      {filterOptions.categories?.map((cat) => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                  {filters.categories?.length > 0 && (
                    <span className="text-xs text-blue-600 mt-1 block">
                      {filters.categories.length} selected
                    </span>
                  )}
                </motion.div>

                {/* Channel */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <label className="filter-label">Channel</label>
                  <div className="relative">
                    <select
                      data-testid="filter-channel"
                      multiple
                      value={filters.channels || []}
                      onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions, option => option.value);
                        onFilterChange("channels", selected);
                      }}
                      className="filter-select h-auto min-h-[40px] max-h-[120px]"
                    >
                      {filterOptions.channels?.map((ch) => (
                        <option key={ch} value={ch}>{ch}</option>
                      ))}
                    </select>
                  </div>
                  {filters.channels?.length > 0 && (
                    <span className="text-xs text-blue-600 mt-1 block">
                      {filters.channels.length} selected
                    </span>
                  )}
                </motion.div>

                {/* Region */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 }}
                >
                  <label className="filter-label">Region</label>
                  <div className="relative">
                    <select
                      data-testid="filter-region"
                      multiple
                      value={filters.regions || []}
                      onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions, option => option.value);
                        onFilterChange("regions", selected);
                      }}
                      className="filter-select h-auto min-h-[40px] max-h-[120px]"
                    >
                      {filterOptions.regions?.map((reg) => (
                        <option key={reg} value={reg}>{reg}</option>
                      ))}
                    </select>
                  </div>
                  {filters.regions?.length > 0 && (
                    <span className="text-xs text-blue-600 mt-1 block">
                      {filters.regions.length} selected
                    </span>
                  )}
                </motion.div>

                {/* Gap Analysis specific filters */}
                {pageType === "gap-analysis" && (
                  <>
                    {/* Understocking Threshold */}
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                    >
                      <label className="filter-label">
                        Understocking Threshold (≤)
                      </label>
                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          data-testid="filter-understock-threshold"
                          min="-100"
                          max="0"
                          value={filters.understockThreshold ?? -5}
                          onChange={(e) => onFilterChange("understockThreshold", parseInt(e.target.value))}
                          className="flex-1"
                        />
                        <span className="text-sm font-medium text-slate-700 w-12 text-right">
                          {filters.understockThreshold ?? -5}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">Filter for values ≤ threshold</p>
                    </motion.div>

                    {/* Overstocking Threshold */}
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.35 }}
                    >
                      <label className="filter-label">
                        Overstocking Threshold (≥)
                      </label>
                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          data-testid="filter-overstock-threshold"
                          min="0"
                          max="100"
                          value={filters.overstockThreshold ?? 5}
                          onChange={(e) => onFilterChange("overstockThreshold", parseInt(e.target.value))}
                          className="flex-1"
                        />
                        <span className="text-sm font-medium text-slate-700 w-12 text-right">
                          {filters.overstockThreshold ?? 5}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">Filter for values ≥ threshold</p>
                    </motion.div>
                  </>
                )}

                {/* Core Logics specific filters */}
                {pageType === "core-logics" && (
                  <>
                    {/* Min Size (Healthy) */}
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                    >
                      <label className="filter-label">
                        Min Size (Healthy) (≥)
                      </label>
                      <div className="flex items-center gap-3">
                        <input
                          type="number"
                          data-testid="filter-min-size"
                          min="0"
                          max="100"
                          value={filters.minSize ?? 0}
                          onChange={(e) => onFilterChange("minSize", parseInt(e.target.value) || 0)}
                          className="filter-input"
                          placeholder="0"
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-1">Filter for sizes ≥ value</p>
                    </motion.div>

                    {/* Min Size % (Healthy) */}
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.35 }}
                    >
                      <label className="filter-label">
                        Min Size % (Healthy) (≥)
                      </label>
                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          data-testid="filter-min-size-percent"
                          min="0"
                          max="100"
                          value={filters.minSizePercent ?? 0}
                          onChange={(e) => onFilterChange("minSizePercent", parseInt(e.target.value))}
                          className="flex-1"
                        />
                        <span className="text-sm font-medium text-slate-700 w-12 text-right">
                          {filters.minSizePercent ?? 0}%
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">Filter for size % ≥ value</p>
                    </motion.div>
                  </>
                )}
              </div>

              {/* Info Bar */}
              <div className="flex items-center justify-between text-xs text-slate-500 mb-4 pb-4 border-b border-slate-100">
                <span>
                  Data Considered: {filters.startDate || 'All'} to {filters.endDate || 'All'}
                </span>
                <span>
                  Hold Ctrl/Cmd to select multiple options
                </span>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between">
                <button
                  data-testid="filter-reset-btn"
                  onClick={onReset}
                  className="btn-secondary flex items-center gap-2"
                >
                  <X size={16} />
                  Reset Filters
                </button>
                <button
                  data-testid="filter-apply-btn"
                  onClick={() => {
                    onApply();
                    setIsOpen(false);
                  }}
                  className="btn-primary"
                >
                  Apply Filters
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default FilterPanel;
