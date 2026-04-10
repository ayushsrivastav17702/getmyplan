import { useState } from "react";
import { X, Send, CheckCircle } from "lucide-react";

export default function ContactModal({ isOpen, onClose }) {
  const [form, setForm] = useState({ name: "", email: "", company: "", heardFrom: "", goals: "" });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await new Promise((r) => setTimeout(r, 1000));
    setSubmitted(true);
    setLoading(false);
    setTimeout(() => { setSubmitted(false); onClose(); setForm({ name: "", email: "", company: "", heardFrom: "", goals: "" }); }, 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] overflow-y-auto">
      <div className="fixed inset-0 bg-black/50 transition-opacity" onClick={onClose} />
      <div className="relative min-h-screen flex items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-xl max-w-lg w-full p-6 animate-fadeIn" data-testid="contact-modal">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Request a Demo</h2>
            <button onClick={onClose} data-testid="contact-modal-close" className="text-gray-400 hover:text-gray-600"><X className="h-5 w-5" /></button>
          </div>
          <p className="text-gray-600 mb-6 text-sm">Tell us about your business and we'll schedule a personalized demo within 24 hours.</p>

          {submitted ? (
            <div className="text-center py-8" data-testid="contact-success">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Thank you!</h3>
              <p className="text-gray-600">Our sales team will contact you shortly.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                <input type="text" required value={form.name} onChange={(e) => set("name", e.target.value)} data-testid="contact-name"
                  id="demo-name" name="fullName" autoComplete="name"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" placeholder="Rahul Sharma" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email Address *</label>
                <input type="email" required value={form.email} onChange={(e) => set("email", e.target.value)} data-testid="contact-email"
                  id="demo-email" name="email" autoComplete="email"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" placeholder="rahul@fashionhub.com" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Company Name *</label>
                <input type="text" required value={form.company} onChange={(e) => set("company", e.target.value)} data-testid="contact-company"
                  id="demo-company" name="companyName" autoComplete="organization"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" placeholder="FashionHub" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">How did you hear about us? *</label>
                <select required value={form.heardFrom} onChange={(e) => set("heardFrom", e.target.value)} data-testid="contact-source"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm">
                  <option value="">Select an option</option>
                  <option value="google">Google Search</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="referral">Referral</option>
                  <option value="instagram">Instagram</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">What are your business goals? *</label>
                <textarea required rows={3} value={form.goals} onChange={(e) => set("goals", e.target.value)} data-testid="contact-goals"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  placeholder="e.g., Reduce stockouts, improve forecasting, optimize inventory across 20 stores..." />
              </div>
              <button type="submit" disabled={loading} data-testid="contact-submit"
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                {loading ? <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" /> : <><Send className="h-4 w-4" /> Request Demo</>}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
