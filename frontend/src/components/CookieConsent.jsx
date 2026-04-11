import { useState, useEffect } from 'react';
import { Shield, X } from 'lucide-react';
import { Link } from 'react-router-dom';

const CookieConsent = () => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('cookie_consent');
    if (!consent) {
      const timer = setTimeout(() => setVisible(true), 1200);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('cookie_consent', 'accepted');
    setVisible(false);
  };

  const handleDecline = () => {
    localStorage.setItem('cookie_consent', 'declined');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      data-testid="cookie-consent-banner"
      className="fixed bottom-0 left-0 right-0 z-[9998] animate-slideUp"
      style={{ animation: 'slideUp 0.4s ease-out' }}
    >
      <div className="bg-slate-900 border-t border-slate-700 shadow-2xl">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 sm:py-5">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex items-start gap-3 flex-1">
              <Shield size={22} className="text-blue-400 mt-0.5 shrink-0" />
              <div>
                <p className="text-white text-sm leading-relaxed">
                  This website stores cookies on your computer. These cookies are used to improve your website experience and provide more personalized services to you, both on this website and through other media. To find out more about the cookies we use, see our{' '}
                  <Link to="/privacy" className="text-blue-400 underline underline-offset-2 hover:text-blue-300 transition-colors">
                    Privacy Policy
                  </Link>.
                </p>
                <p className="text-slate-400 text-xs mt-1.5 leading-relaxed">
                  We won't track your information when you visit our site. But in order to comply with your preferences, we'll have to use just one tiny cookie so that you're not asked to make this choice again.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2.5 shrink-0 w-full sm:w-auto">
              <button
                data-testid="cookie-accept-btn"
                onClick={handleAccept}
                className="flex-1 sm:flex-none px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
              >
                Accept
              </button>
              <button
                data-testid="cookie-decline-btn"
                onClick={handleDecline}
                className="flex-1 sm:flex-none px-5 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium rounded-lg transition-colors"
              >
                Decline
              </button>
              <button
                data-testid="cookie-close-btn"
                onClick={handleDecline}
                className="p-1.5 text-slate-500 hover:text-slate-300 transition-colors hidden sm:block"
                aria-label="Close"
              >
                <X size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CookieConsent;
