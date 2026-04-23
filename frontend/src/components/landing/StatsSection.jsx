import { useEffect, useRef, useState } from "react";

const STATS = [
  { target: 92.7, suffix: "%", label: "Forecast Accuracy", desc: "Backtested on 50+ datasets" },
  { target: 41, suffix: "%", label: "Stockout Reduction", desc: "Based on beta results" },
  { target: 32, suffix: "%", label: "Dead Stock Reduction", desc: "Based on beta results" },
  { target: 4.9, suffix: "", label: "User Rating", desc: "Out of 5 stars" },
];

function AnimatedCounter({ target, suffix, started }) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!started) return;
    let current = 0;
    const step = target / 60;
    const iv = setInterval(() => {
      current += step;
      if (current >= target) { setValue(target); clearInterval(iv); }
      else setValue(current);
    }, 25);
    return () => clearInterval(iv);
  }, [started, target]);
  const display = target % 1 !== 0 ? value.toFixed(1) : Math.ceil(value);
  return <span>{display}{suffix}{target === 4.9 ? " / 5" : ""}</span>;
}

export default function StatsSection() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVisible(true); obs.disconnect(); } }, { threshold: 0.3 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <section ref={ref} className="relative py-16 bg-black/20" data-testid="stats-section">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {STATS.map((s) => (
          <div key={s.label} className="bg-white/[0.04] backdrop-blur-sm rounded-2xl border border-indigo-500/10 p-6 text-center hover:bg-white/[0.06] transition-colors" data-testid={`stat-${s.label.toLowerCase().replace(/\s/g, "-")}`}>
            <div className="text-3xl sm:text-4xl font-extrabold text-indigo-400 mb-1">
              <AnimatedCounter target={s.target} suffix={s.suffix} started={visible} />
            </div>
            <div className="text-sm text-slate-300 font-medium">{s.label}</div>
            <div className="text-[11px] text-slate-400 mt-1">{s.desc}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
