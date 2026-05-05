"use client";

import { useState, useRef, useEffect } from "react";
import { Send, User, BookOpen, Sparkles, RefreshCw } from "lucide-react";
import { useLanguage } from "@/components/LanguageProvider";

type Citation = {
    index: number;
    act_name: string;
    section_number: string;
    title: string;
    content_snippet: string;
};

type Message = {
    role: "user" | "assistant";
    content: string;
    citations?: Citation[];
    isLoading?: boolean;
};

export default function ResearchPage() {
    const { t } = useLanguage();
    const [query, setQuery] = useState("");
    const [messages, setMessages] = useState<Message[]>([
        {
            role: "assistant",
            content: "Hello! I'm your AI Legal Assistant. Ask me anything about the Indian Justice Code (BNS), BNSS, or BSA."
        }
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    /* State for filters */
    const [domainFilter, setDomainFilter] = useState("all");
    const [expandedCitation, setExpandedCitation] = useState<Citation | null>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!query.trim() || isLoading) return;

        const userMsg: Message = { role: "user", content: query };
        setMessages(prev => [...prev, userMsg]);
        setQuery("");
        setIsLoading(true);

        const aiPlaceholder: Message = {
            role: "assistant",
            content: "Thinking...",
            isLoading: true
        };
        setMessages(prev => [...prev, aiPlaceholder]);

        try {
            const apiFilter = domainFilter === "all" ? null : domainFilter.toUpperCase();

            const response = await fetch("http://127.0.0.1:8000/api/chat/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: userMsg.content,
                    act_filter: apiFilter,
                    top_k: 5
                })
            });

            if (!response.ok) throw new Error("API Request failed");

            const data = await response.json();

            setMessages(prev => {
                const newMsgs = [...prev];
                newMsgs.pop(); // Remove placeholder
                newMsgs.push({
                    role: "assistant",
                    content: data.answer,
                    citations: data.citations
                });
                return newMsgs;
            });

        } catch (error) {
            console.error("Chat error:", error);
            setMessages(prev => {
                const newMsgs = [...prev];
                newMsgs.pop();
                newMsgs.push({
                    role: "assistant",
                    content: "I apologize, but I encountered an error providing an answer. Please check the backend connection."
                });
                return newMsgs;
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="h-full flex flex-col relative max-w-5xl mx-auto overflow-hidden bg-white dark:bg-zinc-950">

            {/* Header - Sticky & Solid */}
            <div className="flex-none px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-xl z-20 sticky top-0 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-orange-100 dark:bg-orange-500/10 rounded-lg text-orange-600 dark:text-orange-400">
                        <BookOpen className="w-5 h-5" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold font-heading tracking-tight text-zinc-900 dark:text-zinc-100">
                            Legal Research
                        </h2>
                        <p className="text-xs text-zinc-500 dark:text-zinc-400 font-medium tracking-wide uppercase">
                            AI-Powered Case Analysis
                        </p>
                    </div>
                </div>

                {/* Regulatory Domain Filter */}
                <div className="relative">
                    <select
                        value={domainFilter}
                        onChange={(e) => setDomainFilter(e.target.value)}
                        className="appearance-none bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg px-4 py-2 pr-10 text-sm font-medium focus:ring-2 focus:ring-orange-500/20 outline-none cursor-pointer hover:border-orange-500/50 transition-colors text-zinc-700 dark:text-zinc-300 shadow-sm"
                    >
                        <option value="all">All Acts</option>
                        <option value="bns">BNS (Penal Code)</option>
                        <option value="bnss">BNSS (Procedure)</option>
                        <option value="bsa">BSA (Evidence)</option>
                        <option value="ipc">IPC (Legacy)</option>
                        <option value="crpc">CrPC (Legacy)</option>
                        <option value="iea">IEA (Legacy)</option>
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-400">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6" /></svg>
                    </div>
                </div>
            </div>

            {/* Messages Area - Scrollable */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 pb-40 custom-scrollbar relative z-10">
                {/* Subtle Background Pattern inside scroll area */}
                <div className="absolute inset-0 pointer-events-none opacity-40 dark:opacity-20 z-0">
                    <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-orange-100 dark:bg-orange-900/10 rounded-full blur-[100px]" />
                </div>

                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex gap-4 relative z-10 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                    >
                        {/* Avatar */}
                        <div className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center shadow-sm ${msg.role === "assistant"
                            ? "bg-orange-100 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-500/20"
                            : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700"
                            }`}>
                            {msg.role === "assistant" ? <Sparkles className="w-4 h-4" /> : <User className="w-4 h-4" />}
                        </div>

                        {/* Content */}
                        <div className={`flex flex-col gap-2 max-w-2xl ${msg.role === "user" ? "items-end" : "items-start"}`}>
                            <div
                                className={`px-5 py-4 rounded-2xl text-base leading-7 shadow-sm ${msg.role === "user"
                                    ? "bg-orange-600 text-white rounded-tr-sm"
                                    : "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-800 dark:text-zinc-200 rounded-tl-sm"
                                    }`}
                            >
                                {msg.isLoading ? (
                                    <div className="flex gap-1.5 p-1 items-center h-6">
                                        <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" />
                                        <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce delay-75" />
                                        <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce delay-150" />
                                    </div>
                                ) : (
                                    <div className="markdown-content">
                                        {msg.content.split("**").map((part, i) =>
                                            i % 2 === 1 ? (
                                                <strong key={i} className={msg.role === 'user' ? 'text-white font-bold' : 'text-zinc-900 dark:text-white font-semibold'}>
                                                    {part}
                                                </strong>
                                            ) : part
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Citations - Clean Grid */}
                            {msg.role === "assistant" && msg.citations && msg.citations.length > 0 && (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 w-full">
                                    {msg.citations.map((citation, i) => (
                                        <button
                                            key={i}
                                            onClick={() => setExpandedCitation(citation)}
                                            className="group flex items-start gap-3 p-3 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:border-orange-500/50 transition-all hover:shadow-md text-left w-full"
                                        >
                                            <div className="mt-0.5 w-6 h-6 rounded bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400 flex items-center justify-center text-xs font-bold flex-shrink-0">
                                                §
                                            </div>
                                            <div className="min-w-0">
                                                <div className="flex items-center gap-2 mb-0.5">
                                                    <span className="text-[10px] font-bold uppercase tracking-wider text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-500/10 px-1.5 py-0.5 rounded">
                                                        {citation.act_name} {citation.section_number && citation.section_number !== "N/A" ? citation.section_number : ""}
                                                    </span>
                                                </div>
                                                <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate w-full">
                                                    {citation.title || "Section Details"}
                                                </p>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Dock - Clean & Floating */}
            <div className="fixed bottom-6 left-0 right-0 flex justify-center px-4 z-50 pointer-events-none">
                <div className="w-full max-w-3xl pointer-events-auto">
                    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-2 shadow-2xl shadow-zinc-200/50 dark:shadow-black/50 flex items-center gap-2">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleSend()}
                            placeholder={t.research.placeholder || "Ask a legal question..."}
                            disabled={isLoading}
                            className="flex-1 bg-transparent border-none focus:ring-0 text-base font-medium px-4 py-3 placeholder:text-zinc-400 text-zinc-900 dark:text-zinc-100"
                        />
                        <button
                            onClick={handleSend}
                            disabled={!query.trim() || isLoading}
                            className={`p-3 rounded-xl transition-all duration-200 ${!query.trim() || isLoading
                                ? "bg-zinc-100 text-zinc-300 dark:bg-zinc-800 dark:text-zinc-600"
                                : "bg-orange-600 text-white shadow-lg shadow-orange-500/20 hover:bg-orange-700 active:scale-95"
                                }`}
                        >
                            {isLoading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Citation Modal */}
            {expandedCitation && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setExpandedCitation(null)}>
                    <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200 border border-zinc-200 dark:border-zinc-800" onClick={e => e.stopPropagation()}>
                        <div className="p-6 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between bg-zinc-50 dark:bg-zinc-900/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-orange-100 dark:bg-orange-500/10 rounded-lg text-orange-600 dark:text-orange-400 font-bold">
                                    §
                                </div>
                                <div>
                                    <h3 className="font-bold text-lg text-zinc-900 dark:text-zinc-100">
                                        {expandedCitation.act_name}
                                    </h3>
                                    <p className="text-sm font-medium text-orange-600 dark:text-orange-400">
                                        Section {expandedCitation.section_number}
                                    </p>
                                </div>
                            </div>
                            <button onClick={() => setExpandedCitation(null)} className="p-2 hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded-full transition-colors text-zinc-500">
                                <span className="sr-only">Close</span>
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                            </button>
                        </div>
                        <div className="p-6 overflow-y-auto custom-scrollbar">
                            <h4 className="font-semibold text-zinc-900 dark:text-zinc-100 mb-4 text-base border-b border-zinc-100 dark:border-zinc-800 pb-2">
                                {expandedCitation.title}
                            </h4>
                            <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap font-serif">
                                {expandedCitation.content_snippet}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
