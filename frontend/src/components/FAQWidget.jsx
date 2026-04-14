import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import "./FAQWidget.css";
import { MessageCircle, X, Send, Loader2, Bot, User, Trash2 } from "lucide-react";

const FAQ_SUGGESTIONS = [
  "How do I upload my data?",
  "What file format do I need?",
  "How accurate is the AI forecast?",
  "What does DOH mean?",
  "How to fix a stockout?",
];

export const FAQWidget = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const initMessages = () => [{
    role: "assistant",
    content: "Hi! I can answer common questions about GetMyPlan.\n\nAsk me about uploading data, reading dashboards, AI forecasts, or anything else!",
  }];

  const handleOpen = () => {
    if (!open && messages.length === 0) setMessages(initMessages());
    setOpen(true);
  };

  const send = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((p) => [...p, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const res = await axios.post(`${API}/chat`, { message: msg, session_id: sessionId });
      setSessionId(res.data.session_id);
      setMessages((p) => [...p, { role: "assistant", content: res.data.response }]);
    } catch {
      setMessages((p) => [...p, { role: "assistant", content: "Sorry, I couldn't process that. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const clear = () => { setMessages(initMessages()); setSessionId(null); };

  return (
    <>
      {/* Floating trigger button */}
      {!open && (
        <button data-testid="faq-widget-trigger" className="faq-trigger" onClick={handleOpen}>
          <MessageCircle size={22} />
          <span>FAQ</span>
        </button>
      )}

      {/* Chat panel */}
      {open && (
        <div data-testid="faq-widget-panel" className="faq-panel">
          <div className="faq-panel-header">
            <Bot size={18} />
            <span>GetMyPlan Assistant</span>
            <div className="faq-panel-actions">
              <button onClick={clear} title="Clear chat"><Trash2 size={14} /></button>
              <button onClick={() => setOpen(false)} title="Close"><X size={16} /></button>
            </div>
          </div>

          <div className="faq-panel-body">
            {messages.map((m, i) => (
              <div key={i} className={`faq-msg ${m.role}`}>
                <div className="faq-msg-icon">
                  {m.role === "assistant" ? <Bot size={14} /> : <User size={14} />}
                </div>
                <div className="faq-msg-text">{m.content}</div>
              </div>
            ))}
            {loading && (
              <div className="faq-msg assistant">
                <div className="faq-msg-icon"><Bot size={14} /></div>
                <div className="faq-msg-text faq-typing"><Loader2 size={14} className="faq-spin" /> Thinking...</div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Suggestions (only when few messages) */}
          {messages.length <= 1 && !loading && (
            <div className="faq-suggestions">
              {FAQ_SUGGESTIONS.map((q, i) => (
                <button key={i} onClick={() => send(q)}>{q}</button>
              ))}
            </div>
          )}

          <div className="faq-panel-input">
            <input
              data-testid="faq-widget-input"
              type="text"
              placeholder="Type your question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())}
            />
            <button data-testid="faq-widget-send" onClick={() => send()} disabled={!input.trim() || loading}>
              <Send size={16} />
            </button>
          </div>

          <div className="faq-panel-footer">
            Need human help?{" "}
            <button onClick={() => window.Tawk_API?.maximize?.()}>Chat with Support</button>
          </div>
        </div>
      )}
    </>
  );
};
