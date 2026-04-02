import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Filter, ChevronDown, ChevronUp, X, Calendar, Save, 
  Star, Trash2, Tag, BookmarkPlus, Settings2, Upload, Download
} from "lucide-react";
import axios from "axios";
import { API } from "../App";

const FilterPanel = ({ 
  filters, 
  filterOptions, 
  onFilterChange, 
  onApply, 
  onReset,
  onLoadPreset,
  pageType = "common"
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [showPresetModal, setShowPresetModal] = useState(false);
  const [showPresetList, setShowPresetList] = useState(false);
  const [teamPresets, setTeamPresets] = useState([]);
  const [personalPresets, setPersonalPresets] = useState([]);
  const [allTags, setAllTags] = useState([]);
  const [newPreset, setNewPreset] = useState({
    name: "",
    description: "",
    tags: [],
    isTeam: false
  });
  const [newTag, setNewTag] = useState("");

  // Load presets on mount
  useEffect(() => {
    fetchTeamPresets();
    loadPersonalPresets();
    fetchAllTags();
  }, [pageType]);

  const fetchTeamPresets = async () => {
    try {
      const response = await axios.get(`${API}/presets?page_type=${pageType}`);
      setTeamPresets(response.data || []);
    } catch (err) {
      console.error("Error fetching team presets:", err);
    }
  };

  const fetchAllTags = async () => {
    try {
      const response = await axios.get(`${API}/presets/tags/all`);
      setAllTags(response.data || []);
    } catch (err) {
      console.error("Error fetching tags:", err);
    }
  };

  const loadPersonalPresets = () => {
    const key = `filter_presets_${pageType}`;
    const stored = localStorage.getItem(key);
    if (stored) {
      setPersonalPresets(JSON.parse(stored));
    }
  };

  const savePersonalPreset = (preset) => {
    const key = `filter_presets_${pageType}`;
    const updated = [...personalPresets, { ...preset, id: Date.now().toString() }];
    localStorage.setItem(key, JSON.stringify(updated));
    setPersonalPresets(updated);
  };

  const deletePersonalPreset = (presetId) => {
    const key = `filter_presets_${pageType}`;
    const updated = personalPresets.filter(p => p.id !== presetId);
    localStorage.setItem(key, JSON.stringify(updated));
    setPersonalPresets(updated);
  };

  const togglePersonalFavorite = (presetId) => {
    const key = `filter_presets_${pageType}`;
    const updated = personalPresets.map(p => 
      p.id === presetId ? { ...p, is_favorite: !p.is_favorite } : p
    );
    localStorage.setItem(key, JSON.stringify(updated));
    setPersonalPresets(updated);
  };

  // Count active filters
  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.startDate) count++;
    if (filters.endDate) count++;
    if (filters.categories?.length > 0) count++;
    if (filters.channels?.length > 0) count++;
    if (filters.regions?.length > 0) count++;
    if (pageType === "gap-analysis") {
      if (filters.understockThreshold !== undefined && filters.understockThreshold !== -5) count++;
      if (filters.overstockThreshold !== undefined && filters.overstockThreshold !== 5) count++;
    }
    if (pageType === "core-logics") {
      if (filters.minSize !== undefined && filters.minSize !== 0) count++;
      if (filters.minSizePercent !== undefined && filters.minSizePercent !== 0) count++;
    }
    return count;
  };

  const activeCount = getActiveFilterCount();

  // Get favorite presets for quick access pills
  const favoritePresets = [
    ...personalPresets.filter(p => p.is_favorite),
    ...teamPresets.filter(p => p.is_favorite)
  ];

  const handleSavePreset = async () => {
    if (!newPreset.name.trim()) return;

    const presetData = {
      name: newPreset.name,
      description: newPreset.description,
      tags: newPreset.tags,
      page_type: pageType,
      filters: { ...filters },
      is_favorite: false
    };

    if (newPreset.isTeam) {
      // Save to MongoDB
      try {
        await axios.post(`${API}/presets`, presetData);
        await fetchTeamPresets();
      } catch (err) {
        console.error("Error saving team preset:", err);
      }
    } else {
      // Save to localStorage
      savePersonalPreset(presetData);
    }

    setNewPreset({ name: "", description: "", tags: [], isTeam: false });
    setShowPresetModal(false);
  };

  const handleLoadPreset = (preset) => {
    // Apply the preset filters
    Object.entries(preset.filters).forEach(([key, value]) => {
      onFilterChange(key, value);
    });
    setShowPresetList(false);
    onApply();
  };

  const handleDeleteTeamPreset = async (presetId) => {
    try {
      await axios.delete(`${API}/presets/${presetId}`);
      await fetchTeamPresets();
    } catch (err) {
      console.error("Error deleting preset:", err);
    }
  };

  const handleToggleTeamFavorite = async (presetId) => {
    try {
      await axios.patch(`${API}/presets/${presetId}/favorite`);
      await fetchTeamPresets();
    } catch (err) {
      console.error("Error toggling favorite:", err);
    }
  };

  const handleExportPresets = async () => {
    try {
      const response = await axios.get(`${API}/presets/export?page_type=${pageType}`);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `presets_${pageType}_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Error exporting presets:", err);
    }
  };

  const handleImportPresets = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      await axios.post(`${API}/presets/import`, { presets: data.presets || data });
      await fetchTeamPresets();
      e.target.value = '';
    } catch (err) {
      console.error("Error importing presets:", err);
      e.target.value = '';
    }
  };

  const addTag = () => {
    if (newTag.trim() && !newPreset.tags.includes(newTag.trim())) {
      setNewPreset(prev => ({ ...prev, tags: [...prev.tags, newTag.trim()] }));
      setNewTag("");
    }
  };

  const removeTag = (tag) => {
    setNewPreset(prev => ({ ...prev, tags: prev.tags.filter(t => t !== tag) }));
  };

  return (
    <div className="mb-6">
      {/* Favorite Presets Quick Access Pills */}
      {favoritePresets.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 self-center mr-2">
            Quick Filters:
          </span>
          {favoritePresets.map((preset) => (
            <button
              key={preset.id}
              data-testid={`quick-preset-${preset.id}`}
              onClick={() => handleLoadPreset(preset)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition-colors border border-blue-200"
            >
              <Star size={12} className="fill-current" />
              {preset.name}
            </button>
          ))}
        </div>
      )}

      {/* Filter Trigger */}
      <button
        data-testid="filter-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
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
        <div className="flex items-center gap-3">
          {/* Preset Quick Actions */}
          <button
            data-testid="presets-dropdown-btn"
            onClick={(e) => { e.stopPropagation(); setShowPresetList(!showPresetList); }}
            className="flex items-center gap-1 px-3 py-1 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded transition-colors"
          >
            <BookmarkPlus size={14} />
            Presets
            <ChevronDown size={14} />
          </button>
          
          {isOpen ? (
            <ChevronUp size={20} className="text-slate-400" />
          ) : (
            <ChevronDown size={20} className="text-slate-400" />
          )}
        </div>
      </button>

      {/* Presets Dropdown */}
      <AnimatePresence>
        {showPresetList && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute right-0 mt-1 w-80 bg-white border border-slate-200 rounded shadow-lg z-50"
            style={{ marginTop: '4px' }}
          >
            <div className="p-3 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-slate-900">Saved Presets</h4>
                <button
                  onClick={() => setShowPresetList(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            <div className="max-h-80 overflow-y-auto">
              {/* Personal Presets */}
              {personalPresets.length > 0 && (
                <div className="p-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-2">
                    Personal
                  </span>
                  {personalPresets.map((preset) => (
                    <div
                      key={preset.id}
                      className="flex items-center justify-between p-2 hover:bg-slate-50 rounded cursor-pointer group"
                    >
                      <div 
                        className="flex-1"
                        onClick={() => handleLoadPreset(preset)}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-slate-700">{preset.name}</span>
                          {preset.is_favorite && <Star size={12} className="text-amber-400 fill-current" />}
                        </div>
                        {preset.description && (
                          <p className="text-xs text-slate-500 truncate">{preset.description}</p>
                        )}
                        {preset.tags?.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {preset.tags.slice(0, 3).map(tag => (
                              <span key={tag} className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => { e.stopPropagation(); togglePersonalFavorite(preset.id); }}
                          className="p-1 hover:bg-slate-200 rounded"
                        >
                          <Star size={14} className={preset.is_favorite ? "text-amber-400 fill-current" : "text-slate-400"} />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); deletePersonalPreset(preset.id); }}
                          className="p-1 hover:bg-red-100 rounded text-slate-400 hover:text-red-500"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Team Presets */}
              {teamPresets.length > 0 && (
                <div className="p-2 border-t border-slate-100">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-2">
                    Team
                  </span>
                  {teamPresets.map((preset) => (
                    <div
                      key={preset.id}
                      className="flex items-center justify-between p-2 hover:bg-slate-50 rounded cursor-pointer group"
                    >
                      <div 
                        className="flex-1"
                        onClick={() => handleLoadPreset(preset)}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-slate-700">{preset.name}</span>
                          {preset.is_favorite && <Star size={12} className="text-amber-400 fill-current" />}
                        </div>
                        {preset.description && (
                          <p className="text-xs text-slate-500 truncate">{preset.description}</p>
                        )}
                        {preset.tags?.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {preset.tags.slice(0, 3).map(tag => (
                              <span key={tag} className="text-[10px] px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleToggleTeamFavorite(preset.id); }}
                          className="p-1 hover:bg-slate-200 rounded"
                        >
                          <Star size={14} className={preset.is_favorite ? "text-amber-400 fill-current" : "text-slate-400"} />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDeleteTeamPreset(preset.id); }}
                          className="p-1 hover:bg-red-100 rounded text-slate-400 hover:text-red-500"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Empty State */}
              {personalPresets.length === 0 && teamPresets.length === 0 && (
                <div className="p-6 text-center">
                  <BookmarkPlus size={24} className="mx-auto text-slate-300 mb-2" />
                  <p className="text-sm text-slate-500">No presets saved yet</p>
                  <p className="text-xs text-slate-400">Save your current filters as a preset</p>
                </div>
              )}
            </div>

            {/* Save New Preset Button */}
            <div className="p-3 border-t border-slate-100 space-y-2">
              <button
                data-testid="open-save-preset-btn"
                onClick={() => { setShowPresetList(false); setShowPresetModal(true); }}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded transition-colors"
              >
                <Save size={16} />
                Save Current Filters as Preset
              </button>
              <div className="flex gap-2">
                <button
                  data-testid="export-presets-btn"
                  onClick={handleExportPresets}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 border border-slate-200 rounded transition-colors"
                >
                  <Download size={14} />
                  Export
                </button>
                <label
                  data-testid="import-presets-btn"
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 border border-slate-200 rounded transition-colors cursor-pointer"
                >
                  <Upload size={14} />
                  Import
                  <input type="file" accept=".json" onChange={handleImportPresets} className="hidden" />
                </label>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Save Preset Modal */}
      <AnimatePresence>
        {showPresetModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/30 flex items-center justify-center z-50"
            onClick={() => setShowPresetModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4"
            >
              <div className="p-4 border-b border-slate-200">
                <h3 className="text-lg font-semibold text-slate-900">Save Filter Preset</h3>
              </div>
              
              <div className="p-4 space-y-4">
                {/* Name */}
                <div>
                  <label className="filter-label">Preset Name *</label>
                  <input
                    type="text"
                    data-testid="preset-name-input"
                    value={newPreset.name}
                    onChange={(e) => setNewPreset(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g., North Region Q1 Analysis"
                    className="filter-input"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="filter-label">Description</label>
                  <textarea
                    data-testid="preset-description-input"
                    value={newPreset.description}
                    onChange={(e) => setNewPreset(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Brief description of this preset..."
                    rows={2}
                    className="filter-input resize-none"
                  />
                </div>

                {/* Tags */}
                <div>
                  <label className="filter-label">Tags</label>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      data-testid="preset-tag-input"
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addTag()}
                      placeholder="Add a tag..."
                      className="filter-input flex-1"
                    />
                    <button
                      onClick={addTag}
                      className="px-3 py-2 text-sm bg-slate-100 hover:bg-slate-200 rounded transition-colors"
                    >
                      <Tag size={16} />
                    </button>
                  </div>
                  {/* Tag suggestions */}
                  {allTags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {allTags.filter(t => !newPreset.tags.includes(t)).slice(0, 5).map(tag => (
                        <button
                          key={tag}
                          onClick={() => setNewPreset(prev => ({ ...prev, tags: [...prev.tags, tag] }))}
                          className="text-xs px-2 py-0.5 bg-slate-50 text-slate-500 hover:bg-slate-100 rounded transition-colors"
                        >
                          + {tag}
                        </button>
                      ))}
                    </div>
                  )}
                  {/* Selected tags */}
                  {newPreset.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {newPreset.tags.map(tag => (
                        <span
                          key={tag}
                          className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded"
                        >
                          {tag}
                          <button onClick={() => removeTag(tag)} className="hover:text-blue-900">
                            <X size={12} />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Save Type */}
                <div>
                  <label className="filter-label">Save To</label>
                  <div className="flex gap-3">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        checked={!newPreset.isTeam}
                        onChange={() => setNewPreset(prev => ({ ...prev, isTeam: false }))}
                        className="text-blue-600"
                      />
                      <span className="text-sm text-slate-700">Personal (this browser)</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        checked={newPreset.isTeam}
                        onChange={() => setNewPreset(prev => ({ ...prev, isTeam: true }))}
                        className="text-blue-600"
                      />
                      <span className="text-sm text-slate-700">Team (shared)</span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="p-4 border-t border-slate-200 flex justify-end gap-3">
                <button
                  onClick={() => setShowPresetModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  data-testid="save-preset-btn"
                  onClick={handleSavePreset}
                  disabled={!newPreset.name.trim()}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Save Preset
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Filter Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="filter-panel">
              {/* Filter Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                {/* Date Range - Start */}
                <div>
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
                </div>

                {/* Date Range - End */}
                <div>
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
                </div>

                {/* Category */}
                <div>
                  <label className="filter-label">Category</label>
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
                  {filters.categories?.length > 0 && (
                    <span className="text-xs text-blue-600 mt-1 block">
                      {filters.categories.length} selected
                    </span>
                  )}
                </div>

                {/* Channel */}
                <div>
                  <label className="filter-label">Channel</label>
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
                  {filters.channels?.length > 0 && (
                    <span className="text-xs text-blue-600 mt-1 block">
                      {filters.channels.length} selected
                    </span>
                  )}
                </div>

                {/* Region */}
                <div>
                  <label className="filter-label">Region</label>
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
                  {filters.regions?.length > 0 && (
                    <span className="text-xs text-blue-600 mt-1 block">
                      {filters.regions.length} selected
                    </span>
                  )}
                </div>

                {/* Gap Analysis specific filters */}
                {pageType === "gap-analysis" && (
                  <>
                    <div>
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
                    </div>

                    <div>
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
                    </div>
                  </>
                )}

                {/* Core Logics specific filters */}
                {pageType === "core-logics" && (
                  <>
                    <div>
                      <label className="filter-label">
                        Min Size (Healthy) (≥)
                      </label>
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

                    <div>
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
                    </div>
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
                <div className="flex items-center gap-3">
                  <button
                    data-testid="filter-reset-btn"
                    onClick={onReset}
                    className="btn-secondary flex items-center gap-2"
                  >
                    <X size={16} />
                    Reset Filters
                  </button>
                  <button
                    data-testid="save-current-filters-btn"
                    onClick={() => setShowPresetModal(true)}
                    className="btn-ghost flex items-center gap-2"
                  >
                    <Save size={16} />
                    Save as Preset
                  </button>
                </div>
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
