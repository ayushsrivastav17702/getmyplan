import { Link } from "react-router-dom";

export default function CTASection() {
  return (
    <section className="relative py-20" data-testid="cta-section">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
        <div className="bg-gradient-to-br from-indigo-500/10 to-rose-500/10 border border-indigo-500/20 rounded-3xl p-10 sm:p-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Ready to stop guessing?</h2>
          <p className="text-lg text-slate-400 mb-8 max-w-lg mx-auto">Join 200+ fashion retailers who replaced spreadsheets with AI-powered demand planning.</p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/signup" className="px-8 py-3.5 bg-gradient-to-r from-indigo-500 to-rose-500 text-white rounded-xl text-base font-semibold shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:-translate-y-0.5 transition-all">
              Start 7-Day Free Trial
            </Link>
            <Link to="/login" className="px-8 py-3.5 border border-slate-600 text-slate-200 rounded-xl text-base font-semibold hover:bg-white/5 transition-all">
              Log in
            </Link>
          </div>
          <p className="text-xs text-slate-400 mt-4">No credit card required</p>
        </div>
      </div>
    </section>
  );
}
