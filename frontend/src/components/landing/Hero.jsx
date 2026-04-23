import { useEffect, useRef, useCallback } from "react";
import { Link } from "react-router-dom";

export default function Hero({ onWatchDemo, onRequestDemo }) {
  const canvasRef = useRef(null);

  // Three.js particle background
  useEffect(() => {
    const container = canvasRef.current;
    if (!container) return;
    let animId;

    const loadThree = async () => {
      try {
        const THREE = await import("three");
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = 30;

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
        renderer.setClearColor(0x000000, 0);
        container.appendChild(renderer.domElement);

        const count = 1500;
        const geo = new THREE.BufferGeometry();
        const pos = new Float32Array(count * 3);
        for (let i = 0; i < count * 3; i += 3) {
          pos[i] = (Math.random() - 0.5) * 100;
          pos[i + 1] = (Math.random() - 0.5) * 60;
          pos[i + 2] = (Math.random() - 0.5) * 50;
        }
        geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
        const mat = new THREE.PointsMaterial({ size: 0.12, color: 0x6366f1, transparent: true, opacity: 0.45 });
        const mesh = new THREE.Points(geo, mat);
        scene.add(mesh);

        const onResize = () => {
          camera.aspect = window.innerWidth / window.innerHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(window.innerWidth, window.innerHeight);
        };
        window.addEventListener("resize", onResize);

        const animate = () => {
          animId = requestAnimationFrame(animate);
          mesh.rotation.x += 0.0003;
          mesh.rotation.y += 0.0004;
          renderer.render(scene, camera);
        };
        animate();

        return () => {
          window.removeEventListener("resize", onResize);
          cancelAnimationFrame(animId);
          renderer.dispose();
          if (container.contains(renderer.domElement)) container.removeChild(renderer.domElement);
        };
      } catch {
        // Three.js not available — fail silently
      }
    };

    let cleanup;
    loadThree().then((c) => { cleanup = c; });
    return () => { if (cleanup) cleanup(); else cancelAnimationFrame(animId); };
  }, []);

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden" data-testid="hero-section">
      {/* Background layers */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0e27] via-[#1a1a3e] to-[#0f172a]" />
      <div ref={canvasRef} className="absolute inset-0 pointer-events-none" />
      {/* Radial glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 text-center pt-28 pb-16">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-sm font-medium mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
          AI-Powered Demand Planning
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold text-white leading-[1.1] tracking-tight mb-6" data-testid="hero-heading">
          Stop Guessing.<br />
          <span className="bg-gradient-to-r from-indigo-400 via-rose-400 to-indigo-400 bg-clip-text text-transparent bg-[length:200%_auto] animate-shimmer">Start Knowing.</span>
        </h1>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed" data-testid="hero-subtitle">
          AI predicts what you'll sell, where, and when &mdash; with <span className="text-white font-semibold">92.7% forecast accuracy</span>.
          Upload 5 CSV files. Get 12-month forecasts, stockout warnings, and purchase orders in 15 minutes.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-8">
          <Link
            to="/signup"
            data-testid="hero-cta-trial"
            className="px-8 py-3.5 bg-gradient-to-r from-indigo-500 to-rose-500 text-white rounded-xl text-base font-semibold shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30 hover:-translate-y-0.5 transition-all"
          >
            Start 7-Day Free Trial
          </Link>
          <button
            onClick={onWatchDemo}
            data-testid="hero-cta-demo"
            className="px-8 py-3.5 border border-slate-600 text-slate-200 rounded-xl text-base font-semibold hover:bg-white/5 hover:border-slate-500 transition-all flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
            Watch Demo
          </button>
        </div>

        <p className="text-xs text-slate-400">No credit card required &middot; 15-minute setup &middot; Cancel anytime</p>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#0a0e27] to-transparent pointer-events-none" />
    </section>
  );
}
