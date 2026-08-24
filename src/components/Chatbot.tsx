import React, { useState, useRef, useEffect } from 'react';
import { Send, X, Sparkles, Loader2, MessageCircle, RotateCcw } from 'lucide-react';

const Chatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([{ role: 'model', content: "Hi! I'm CyberDaksh Learning. How can I assist your CyberLearn journey?" }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { if (isOpen) endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, isLoading, isOpen]);

  const fetchAIResponse = async (userText: string, chatHistory: any[]) => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";

    try {
      const response = await fetch(`${apiUrl}/api/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText, chatHistory: chatHistory })
      });

      const data = await response.json();

      if (response.ok && data.answer) {
        return data.answer;
      } else {
        console.error("Backend error:", data.error);
        return "I'm having trouble connecting to AI. Please check if the backend is running.";
      }
    } catch (err) {
      console.error("Connection error:", err);
      return "I'm having trouble connecting to AI. Please check your internet connection or backend.";
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    const aiReply = await fetchAIResponse(currentInput, messages);
    
    setMessages(prev => [...prev, { role: 'model', content: aiReply }]);
    setIsLoading(false);
  };

  return (
    <div className="fixed bottom-6 right-6 z-[9999] font-sans">
      {isOpen && (
        <div className="mb-4 w-80 sm:w-[400px] h-[550px] bg-white rounded-[2.5rem] shadow-2xl border border-purple-100 flex flex-col overflow-hidden animate-in slide-in-from-bottom-5">
          {/* Header */}
          <div className="bg-[#8B5CF6] p-6 text-white flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Sparkles size={20} />
              <span className="font-bold text-lg">CyberDaksh Learning</span>
            </div>
            <X className="cursor-pointer hover:opacity-70" onClick={() => setIsOpen(false)} />
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-[#F9FAFB] no-scrollbar">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-4 rounded-3xl text-[13px] leading-relaxed shadow-sm ${
                  m.role === 'user' ? 'bg-[#6366F1] text-white rounded-tr-none' : 'bg-white text-slate-700 rounded-tl-none border border-slate-100'
                }`}>
                  {m.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-slate-400 text-[11px] italic ml-2">
                <Loader2 size={14} className="animate-spin text-purple-500" /> DAX is searching course docs...
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Input */}
          <div className="p-5 bg-white border-t border-slate-100 flex gap-2 items-center">
            <input 
              value={input} 
              onChange={e => setInput(e.target.value)} 
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Ask anything..." 
              className="flex-1 bg-slate-100 rounded-2xl px-5 py-3 text-sm outline-none focus:ring-2 focus:ring-purple-300 transition-all" 
            />
            <button 
              onClick={handleSend} 
              disabled={isLoading || !input.trim()}
              className="bg-[#6366F1] text-white p-3 rounded-2xl hover:scale-105 active:scale-95 disabled:bg-slate-300 transition-all"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      )}

      {/* Floating Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)} 
        className="w-16 h-16 bg-[#8B5CF6] text-white rounded-full flex items-center justify-center shadow-xl hover:scale-110 active:scale-95 transition-all"
      >
        {isOpen ? <X size={28} /> : <MessageCircle size={28} />}
      </button>
    </div>
  );
};

export default Chatbot;
