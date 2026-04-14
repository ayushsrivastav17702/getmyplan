import { useState, useEffect } from "react";
import "./OnboardingChecklist.css";
import { CheckCircle, Circle, ArrowRight, X, ChevronDown, ChevronUp, MessageCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";

const STEPS = [
  { id: "sample_data", label: "Load sample data", desc: "See how GetMyPlan works with demo data (30 seconds)", action: "/upload", check: (s) => s?.sample_data_loaded },
  { id: "sku_master", label: "Upload SKU Master", desc: "Add your products and pricing", action: "/upload", check: (s) => s?.master_data?.sku_master?.uploaded },
  { id: "store_master", label: "Upload Store Master", desc: "Add your store locations", action: "/upload", check: (s) => s?.master_data?.store_master?.uploaded },
  { id: "daily_sales", label: "Upload Daily Sales", desc: "Add 30+ days of sales history", action: "/upload", check: (s) => s?.transactional_data?.daily_sales?.uploaded },
  { id: "store_inventory", label: "Upload Store Inventory", desc: "Add current stock levels", action: "/upload", check: (s) => s?.transactional_data?.store_inventory?.uploaded },
  { id: "view_dashboard", label: "Explore Executive Dashboard", desc: "See your KPIs and stock health", action: "/dashboard", check: (s) => s?.is_onboarded },
  { id: "run_forecast", label: "Generate AI forecast", desc: "Get 12-month demand predictions", action: "/ai-demand", check: (s) => false },
];

export const OnboardingChecklist = ({ status }) => {
  const navigate = useNavigate();
  const [dismissed, setDismissed] = useState(() => localStorage.getItem("gmp_checklist_dismissed") === "true");
  const [collapsed, setCollapsed] = useState(false);

  if (dismissed || !status) return null;

  const completed = STEPS.filter((s) => s.check(status)).length;
  const total = STEPS.length;
  const pct = Math.round((completed / total) * 100);

  const handleDismiss = () => { setDismissed(true); localStorage.setItem("gmp_checklist_dismissed", "true"); };

  if (pct === 100) {
    return (
      <div data-testid="onboarding-complete" className="ob-complete">
        <span className="ob-complete-icon">&#127881;</span>
        <div className="ob-complete-text">
          <h4>You're all set!</h4>
          <p>All steps complete. Ready to scale your inventory planning.</p>
        </div>
        <button onClick={handleDismiss} className="ob-dismiss"><X size={16} /></button>
      </div>
    );
  }

  return (
    <div data-testid="onboarding-checklist" className={`ob-checklist ${collapsed ? "ob-collapsed" : ""}`}>
      <div className="ob-header">
        <div className="ob-header-left">
          <div>
            <h3>Getting Started</h3>
            <p>{completed} of {total} steps complete</p>
          </div>
        </div>
        <div className="ob-header-right">
          <button className="ob-toggle" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
          </button>
          <button className="ob-dismiss" onClick={handleDismiss}><X size={16} /></button>
        </div>
      </div>
      {!collapsed && (
        <>
          <div className="ob-progress-row">
            <div className="ob-progress-track"><div className="ob-progress-fill" style={{ width: `${pct}%` }} /></div>
            <span className="ob-progress-pct">{pct}%</span>
          </div>
          <div className="ob-steps">
            {STEPS.map((step) => {
              const done = step.check(status);
              return (
                <button key={step.id} data-testid={`ob-step-${step.id}`} className={`ob-step ${done ? "done" : ""}`}
                  onClick={() => !done && navigate(step.action)}>
                  {done ? <CheckCircle size={18} className="ob-icon-done" /> : <Circle size={18} className="ob-icon-todo" />}
                  <div className="ob-step-text">
                    <span className="ob-step-label">{step.label}</span>
                    <span className="ob-step-desc">{step.desc}</span>
                  </div>
                  {!done && <ArrowRight size={14} className="ob-step-arrow" />}
                </button>
              );
            })}
          </div>
          <div className="ob-footer">
            <span>Need help?</span>
            <button onClick={() => window.Tawk_API?.maximize?.()}><MessageCircle size={14} /> Chat with us</button>
          </div>
        </>
      )}
    </div>
  );
};
