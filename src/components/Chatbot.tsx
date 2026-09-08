import React, { useState, useRef, useEffect } from 'react';
import { MarkdownRenderer } from './MarkdownRenderer';
import { 
  Send, 
  X, 
  Sparkles, 
  Loader2, 
  MessageCircle, 
  RotateCcw, 
  BookOpen, 
  Bot, 
  User as UserIcon,
  ShieldCheck,
  RefreshCw,
  CheckCircle2,
  Clock,
  Circle,
  Award,
  GraduationCap
} from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'model';
  content: string;
  sources?: string[];
  intent?: string;
  latency_ms?: number;
  timestamp?: string;
  isError?: boolean;
  data?: any;
}

const SUGGESTED_PROMPTS = [
  "What courses am I enrolled in?",
  "What is my progress in Network Security Basics?",
  "What is my score in Firewalls?",
  "Which segments have I completed?",
  "Explain firewalls and tell me my score."
];

const Chatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg_initial',
      role: 'assistant',
      content: "Hello! I am **DAX**, your CyberLearn LMS AI Assistant by CyberDaksh. Ask me about your enrolled courses, segment progress, quiz scores, lab status, or any cybersecurity concepts.",
      sources: []
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, isOpen]);

  const fetchAIResponse = async (userText: string, chatHistory: ChatMessage[]): Promise<{ answer: string; sources: string[]; intent?: string; latency_ms?: number; isError?: boolean; data?: any }> => {
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

    try {
      const token = localStorage.getItem("access_token");

      // Format previous history for backend
      const formattedHistory = chatHistory
        .filter(m => !m.isError)
        .map(m => ({
          role: m.role === 'assistant' ? 'assistant' : 'user',
          content: m.content
        }));

      const response = await fetch(`${API_URL}/api/ai/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ message: userText, chatHistory: formattedHistory })
      });

      const data = await response.json().catch(() => ({}));

      if (response.ok && data.answer) {
        return {
          answer: data.answer,
          sources: Array.isArray(data.sources) ? data.sources : [],
          intent: data.intent,
          latency_ms: data.latency?.total_ms,
          data: data.data
        };
      } else {
        const errorDetail = data.detail || data.error || data.message;
        console.error("Backend error:", errorDetail);
        if (response.status === 401) {
          return {
            answer: "Your session has expired. Please log in again to continue chatting with DAX.",
            sources: [],
            isError: true
          };
        }
        return {
          answer: errorDetail ? `Service notice: ${errorDetail}` : "DAX is temporarily unable to retrieve an answer. Please verify that the backend server is running.",
          sources: [],
          isError: true
        };
      }
    } catch (err) {
      console.error("Connection error:", err);
      return {
        answer: "Connection error: Unable to reach the CyberLearn AI service. Please check your network connection.",
        sources: [],
        isError: true
      };
    }
  };

  const handleSend = async (customPrompt?: string) => {
    const textToSend = (customPrompt || input).trim();
    if (!textToSend || isLoading) return;

    const userMessage: ChatMessage = {
      id: `u_${Date.now()}`,
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const newHistory = [...messages, userMessage];
    setMessages(newHistory);
    setInput('');
    setIsLoading(true);

    const result = await fetchAIResponse(textToSend, newHistory);

    const assistantMessage: ChatMessage = {
      id: `a_${Date.now()}`,
      role: 'assistant',
      content: result.answer,
      sources: result.sources,
      intent: result.intent,
      latency_ms: result.latency_ms,
      isError: result.isError,
      data: result.data,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, assistantMessage]);
    setIsLoading(false);
  };

  const handleResetChat = () => {
    setMessages([
      {
        id: `msg_reset_${Date.now()}`,
        role: 'assistant',
        content: "Conversation history has been reset. How can I assist your CyberLearn studies today?",
        sources: []
      }
    ]);
  };

  return (
    <div className="fixed bottom-6 right-6 z-[9999] font-sans">
      {isOpen && (
        <div className="mb-4 w-[92vw] sm:w-[450px] md:w-[490px] h-[620px] bg-white rounded-[2rem] shadow-2xl border border-purple-100/90 flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-300">
          
          {/* Top Header */}
          <div className="bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-700 p-4 px-5 text-white flex justify-between items-center shadow-xs">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-white/15 backdrop-blur-md flex items-center justify-center border border-white/20 text-purple-100 shadow-inner">
                <Bot size={20} className="text-white" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-[15px] tracking-tight">DAX Assistant</span>
                  <span className="px-1.5 py-0.2 bg-emerald-400/20 text-emerald-300 border border-emerald-400/30 rounded-md text-[9px] font-bold uppercase tracking-wider flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    CyberDaksh LMS
                  </span>
                </div>
                <p className="text-[11px] text-purple-200/90 font-medium">CyberLearn Production AI Assistant</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={handleResetChat}
                title="Reset conversation"
                className="p-2 hover:bg-white/15 rounded-xl text-purple-200 hover:text-white transition-colors"
              >
                <RotateCcw size={16} />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                title="Close chat"
                className="p-2 hover:bg-white/15 rounded-xl text-purple-200 hover:text-white transition-colors"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Messages Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/70">
            {messages.map((m) => {
              const isUser = m.role === 'user';
              return (
                <div key={m.id} className={`flex gap-2.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
                  {!isUser && (
                    <div className={`w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 border ${
                      m.isError ? 'bg-amber-50 text-amber-600 border-amber-200' : 'bg-purple-100 text-purple-600 border-purple-200'
                    }`}>
                      <Sparkles size={14} />
                    </div>
                  )}

                  <div className={`max-w-[88%] rounded-2xl p-4 shadow-2xs text-[13px] leading-relaxed transition-all ${
                    isUser 
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-tr-none shadow-sm' 
                      : m.isError 
                        ? 'bg-amber-50/90 text-amber-900 border border-amber-200 rounded-tl-none' 
                        : 'bg-white text-slate-800 rounded-tl-none border border-slate-200/80 shadow-xs'
                  }`}>
                    {isUser ? (
                      <p className="whitespace-pre-wrap font-medium">{m.content}</p>
                    ) : (
                      <div>
                        {/* Markdown Formatted Answer */}
                        <MarkdownRenderer content={m.content} />

                        {/* Interactive LMS Structured Course Progress Card */}
                        {m.data && m.data.type === 'course_progress' && (
                          <div className="mt-3.5 p-3.5 bg-gradient-to-br from-purple-50/90 via-indigo-50/40 to-white rounded-xl border border-purple-100 shadow-2xs text-slate-800">
                            <div className="flex justify-between items-start mb-2">
                              <div className="flex items-center gap-1.5">
                                <GraduationCap size={16} className="text-purple-600" />
                                <h4 className="font-bold text-[13.5px] text-purple-950">{m.data.course_name}</h4>
                              </div>
                              <span className={`px-2 py-0.5 rounded-full text-[10.5px] font-bold ${
                                m.data.status === 'Completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-purple-100 text-purple-800'
                              }`}>
                                {m.data.status}
                              </span>
                            </div>

                            {/* Progress bar */}
                            <div className="space-y-1 mb-3">
                              <div className="flex justify-between text-[11.5px] font-semibold">
                                <span className="text-purple-900">{m.data.completion_percentage}% Complete</span>
                                <span className="text-slate-600">
                                  Overall Score: <strong className="text-purple-800">{m.data.overall_score !== null ? `${m.data.overall_score}/100` : '—'}</strong>
                                </span>
                              </div>
                              <div className="w-full bg-slate-200/80 h-2 rounded-full overflow-hidden">
                                <div 
                                  className="bg-gradient-to-r from-purple-600 to-indigo-600 h-full rounded-full transition-all duration-500" 
                                  style={{ width: `${Math.min(100, Math.max(0, m.data.completion_percentage))}%` }}
                                />
                              </div>
                              <div className="text-[10.5px] text-slate-500 flex justify-between pt-0.5">
                                <span>{m.data.completed_segments} of {m.data.total_segments} segments completed</span>
                                <span>Last active: {m.data.last_accessed}</span>
                              </div>
                            </div>

                            {/* Segment Breakdown Accordion */}
                            {m.data.segments && m.data.segments.length > 0 && (
                              <div className="mt-2.5 pt-2 border-t border-purple-100/80">
                                <p className="text-[10.5px] font-bold uppercase tracking-wider text-purple-900 mb-1.5 flex items-center gap-1">
                                  <Award size={12} className="text-purple-600" /> Segment Performance Breakdown
                                </p>
                                <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                                  {m.data.segments.map((seg: any, sIdx: number) => (
                                    <div key={sIdx} className="flex items-center justify-between text-[11.5px] py-1 px-2 rounded-lg bg-white/90 border border-purple-100/60 shadow-3xs">
                                      <div className="flex items-center gap-1.5 truncate mr-2">
                                        {seg.status === 'Completed' ? (
                                          <CheckCircle2 size={13} className="text-emerald-600 flex-shrink-0" />
                                        ) : seg.status === 'In Progress' ? (
                                          <Clock size={13} className="text-amber-500 flex-shrink-0" />
                                        ) : (
                                          <Circle size={13} className="text-slate-300 flex-shrink-0" />
                                        )}
                                        <span className="truncate font-medium text-slate-700">
                                          {seg.segment_number}. {seg.segment_name}
                                        </span>
                                      </div>
                                      <div className="flex items-center gap-2 flex-shrink-0">
                                        <span className="font-semibold text-purple-950">
                                          {seg.score !== null ? `${seg.score}%` : '—'}
                                        </span>
                                        <span className={`text-[10px] px-1.5 py-0.2 rounded font-medium ${
                                          seg.status === 'Completed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' :
                                          seg.status === 'In Progress' ? 'bg-amber-50 text-amber-700 border border-amber-100' : 'bg-slate-100 text-slate-500'
                                        }`}>
                                          {seg.status}
                                        </span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Distinct Source Card (Only rendered for general RAG knowledge with sources) */}
                        {m.sources && m.sources.length > 0 && (
                          <div className="mt-3.5 pt-2.5 border-t border-slate-100 flex flex-col gap-1.5">
                            <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                              <BookOpen size={11} className="text-purple-600" />
                              <span>Source</span>
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                              {m.sources.map((src, sIdx) => (
                                <span key={sIdx} className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-100">
                                  {src}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {m.isError && (
                          <div className="mt-2.5 pt-2 border-t border-amber-200/60 flex items-center gap-2">
                            <button
                              onClick={() => handleSend(messages[messages.length - 2]?.content || "Retry")}
                              className="text-[11px] text-purple-700 font-bold hover:underline flex items-center gap-1"
                            >
                              <RefreshCw size={11} /> Retry Inquiry
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="w-7 h-7 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center flex-shrink-0 mt-0.5 border border-indigo-200">
                      <UserIcon size={14} />
                    </div>
                  )}
                </div>
              );
            })}

            {/* Loading / Thinking State */}
            {isLoading && (
              <div className="flex gap-2.5 items-start justify-start animate-in fade-in duration-200">
                <div className="w-7 h-7 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5 border border-purple-200">
                  <Sparkles size={14} className="animate-spin text-purple-600" />
                </div>
                <div className="bg-white border border-slate-200/80 rounded-2xl rounded-tl-none p-3 px-4 shadow-xs flex items-center gap-2">
                  <Loader2 size={15} className="animate-spin text-purple-600" />
                  <span className="text-[12px] font-medium text-slate-500">
                    DAX is analyzing CyberLearn resources...
                  </span>
                </div>
              </div>
            )}

            <div ref={endRef} />
          </div>

          {/* Quick Prompts Carousel */}
          {messages.length <= 2 && !isLoading && (
            <div className="px-4 py-2 bg-white border-t border-slate-100">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <ShieldCheck size={11} className="text-purple-500" /> Suggested LMS Inquiries
              </p>
              <div className="flex gap-1.5 overflow-x-auto no-scrollbar pb-1">
                {SUGGESTED_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(prompt)}
                    className="whitespace-nowrap px-2.5 py-1 bg-purple-50/70 hover:bg-purple-100 text-purple-700 rounded-lg text-[11px] font-medium border border-purple-100 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Box */}
          <div className="p-3.5 bg-white border-t border-slate-100 flex gap-2 items-center">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask about enrolled courses, segment progress, quiz scores, or labs..."
              disabled={isLoading}
              className="flex-1 bg-slate-100/90 rounded-xl px-4 py-2.5 text-[13px] outline-none focus:ring-2 focus:ring-purple-400/50 focus:bg-white transition-all text-slate-800 placeholder:text-slate-400 disabled:opacity-60"
            />
            <button
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              aria-label="Send message"
              className="bg-purple-600 hover:bg-purple-700 active:scale-95 text-white p-2.5 rounded-xl disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed transition-all shadow-xs"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Floating Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? "Close AI assistant" : "Open DAX AI assistant"}
        className="w-14 h-14 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-full flex items-center justify-center shadow-xl hover:scale-105 active:scale-95 transition-all border-2 border-white/20 group"
      >
        {isOpen ? (
          <X size={24} className="group-hover:rotate-90 transition-transform duration-200" />
        ) : (
          <MessageCircle size={26} className="group-hover:scale-110 transition-transform" />
        )}
      </button>
    </div>
  );
};

export default Chatbot;
