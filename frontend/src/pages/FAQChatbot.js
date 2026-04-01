import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Send, Bot, User, Loader2, Trash2, Info } from "lucide-react";

const FAQChatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add initial welcome message
  useEffect(() => {
    setMessages([{
      role: "assistant",
      content: "Hello! I'm your Fashion Retail Gap Analysis assistant. I can help you understand:\n\n• **NOOS Analysis** - Never Out Of Stock optimization\n• **ROS Calculations** - Rate of Sale methodology\n• **Size Set Gap** - Inventory distribution analysis\n• **Platform Features** - How to use the dashboards\n\nWhat would you like to know?"
    }]);
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: userMessage,
        session_id: sessionId
      });

      setSessionId(response.data.session_id);
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: response.data.response 
      }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: "I apologize, but I'm having trouble processing your request. Please try again or check that the backend service is running."
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    setMessages([{
      role: "assistant",
      content: "Chat cleared. How can I help you with the Gap Analysis platform?"
    }]);
    setSessionId(null);
  };

  const suggestedQuestions = [
    "What is NOOS analysis?",
    "How is ROS calculated?",
    "What files do I need to upload?",
    "What is a broken size set?"
  ];

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, i) => {
        // Bold text
        line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Bullet points
        if (line.startsWith('• ') || line.startsWith('- ')) {
          return <li key={i} className="ml-4" dangerouslySetInnerHTML={{ __html: line.substring(2) }} />;
        }
        // Numbered lists
        const numberedMatch = line.match(/^(\d+)\.\s(.+)/);
        if (numberedMatch) {
          return <li key={i} className="ml-4" dangerouslySetInnerHTML={{ __html: numberedMatch[2] }} />;
        }
        return line ? <p key={i} dangerouslySetInnerHTML={{ __html: line }} /> : <br key={i} />;
      });
  };

  return (
    <div className="animate-fade-in-up" data-testid="faq-chatbot-page">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-light tracking-tight text-neutral-900 mb-2">
            FAQ Chatbot
          </h1>
          <p className="text-neutral-500">
            Ask questions about the platform, calculations, and methodology
          </p>
        </div>
        
        <button
          data-testid="clear-chat-btn"
          onClick={handleClear}
          className="flex items-center gap-2 px-4 py-2 text-sm border border-neutral-200 hover:border-neutral-400 transition-colors"
        >
          <Trash2 size={16} />
          Clear Chat
        </button>
      </div>

      {/* Chat Container */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Chat */}
        <div className="lg:col-span-3 bg-white border border-neutral-200 flex flex-col" style={{ height: '600px' }}>
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                data-testid={`chat-message-${i}`}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 flex items-center justify-center bg-[#C4A47C] bg-opacity-20 flex-shrink-0">
                    <Bot size={18} className="text-[#C4A47C]" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] p-4 ${
                    msg.role === 'user'
                      ? 'bg-neutral-900 text-white'
                      : 'bg-neutral-50 text-neutral-700'
                  }`}
                >
                  <div className="text-sm space-y-2">
                    {formatMessage(msg.content)}
                  </div>
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 flex items-center justify-center bg-neutral-900 flex-shrink-0">
                    <User size={18} className="text-white" />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 flex items-center justify-center bg-[#C4A47C] bg-opacity-20 flex-shrink-0">
                  <Bot size={18} className="text-[#C4A47C]" />
                </div>
                <div className="bg-neutral-50 p-4">
                  <Loader2 className="w-5 h-5 animate-spin text-neutral-400" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-neutral-200 p-4">
            <div className="flex gap-3">
              <input
                type="text"
                data-testid="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your question..."
                className="flex-1 input"
                disabled={loading}
              />
              <button
                data-testid="send-message-btn"
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="px-6 py-2 bg-neutral-900 text-white hover:bg-neutral-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Send size={18} />
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Suggested Questions */}
          <div className="bg-white border border-neutral-200 p-4">
            <h3 className="text-sm font-medium text-neutral-900 mb-3">Suggested Questions</h3>
            <div className="space-y-2">
              {suggestedQuestions.map((q, i) => (
                <button
                  key={i}
                  data-testid={`suggested-q-${i}`}
                  onClick={() => setInput(q)}
                  className="w-full text-left text-sm p-2 text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Topics */}
          <div className="bg-white border border-neutral-200 p-4">
            <h3 className="text-sm font-medium text-neutral-900 mb-3">I Can Help With</h3>
            <ul className="space-y-2 text-sm text-neutral-600">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-[#C4A47C]" />
                NOOS Analysis
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-[#C4A47C]" />
                ROS Calculations
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-[#C4A47C]" />
                Size Set Gap
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-[#C4A47C]" />
                Data File Requirements
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-[#C4A47C]" />
                Platform Features
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-[#C4A47C]" />
                Calculation Methodology
              </li>
            </ul>
          </div>

          {/* Info */}
          <div className="bg-neutral-50 border border-neutral-200 p-4">
            <div className="flex items-start gap-2">
              <Info size={16} className="text-neutral-400 mt-0.5" />
              <p className="text-xs text-neutral-500">
                This chatbot is powered by GPT-5.2 and trained on the platform's documentation. For technical issues, please contact support.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FAQChatbot;
