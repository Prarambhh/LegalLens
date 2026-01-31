"use client";

import { useState } from "react";
import { Upload, FileText, X, CheckCircle2, AlertCircle, File, Loader2, Sparkles, BookOpen, Send } from "lucide-react";
import { useLanguage } from "@/components/LanguageProvider";

type UploadState = "idle" | "uploading" | "analyzing" | "complete" | "error";

interface AnalyzedDoc {
    name: string;
    size: string;
    type: string;
    summary: string;
    charges: string[];
    parties: string[];
    date: string;
}

export default function DocumentsPage() {
    const { t } = useLanguage();
    const [dragActive, setDragActive] = useState(false);
    const [uploadState, setUploadState] = useState<UploadState>("idle");
    const [analyzedDoc, setAnalyzedDoc] = useState<AnalyzedDoc | null>(null);
    const [fullText, setFullText] = useState("");
    const [anomalies, setAnomalies] = useState<any[]>([]);
    const [activeTab, setActiveTab] = useState<"analysis" | "chat">("analysis");
    const [chatInput, setChatInput] = useState("");
    const [chatMessages, setChatMessages] = useState<any[]>([
        { role: "assistant", content: "I've analyzed your document. You can ask me questions about specific clauses or legal implications." }
    ]);
    const [isChatLoading, setIsChatLoading] = useState(false);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFiles(e.dataTransfer.files[0]);
        }
    };

    const handleFiles = async (file: File) => {
        setUploadState("uploading");

        // Real API Call
        try {
            const formData = new FormData();
            formData.append("file", file);

            const res = await fetch("http://localhost:8000/api/documents/analyze", {
                method: "POST",
                body: formData
            });

            if (!res.ok) throw new Error("Analysis failed");

            const data = await res.json();

            setFullText(data.full_text || "Document text not returned by server.");
            setAnomalies(data.anomalies || []);

            setAnalyzedDoc({
                name: file.name,
                size: (file.size / 1024 / 1024).toFixed(2) + " MB",
                type: data.document_type || "Unknown Type",
                summary: data.summary,
                charges: data.risks || [], // Map risks to "charges" for now
                parties: data.key_parties || [],
                date: data.dates?.[0] || "N/A"
            });

            setUploadState("complete");

        } catch (error) {
            console.error(error);
            setUploadState("error");
        }
    };

    const handleChatSend = async () => {
        if (!chatInput.trim() || isChatLoading) return;

        const userMsg = { role: "user", content: chatInput };
        setChatMessages(prev => [...prev, userMsg]);
        setChatInput("");
        setIsChatLoading(true);

        try {
            const res = await fetch("http://localhost:8000/api/documents/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: userMsg.content,
                    document_text: fullText
                })
            });

            if (!res.ok) throw new Error("Chat failed");

            const data = await res.json();

            setChatMessages(prev => [...prev, {
                role: "assistant",
                content: data.answer,
                citations: data.citations
            }]);

        } catch (error) {
            console.error(error);
            setChatMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error searching for answers." }]);
        } finally {
            setIsChatLoading(false);
        }
    };

    // Helper to highlight text
    const renderHighlightedText = (text: string, anomalies: any[]) => {
        if (!anomalies?.length) return <p className="whitespace-pre-wrap">{text}</p>;

        let parts: { text: string; anomaly?: any }[] = [{ text }];

        anomalies.forEach(anomaly => {
            const quote = anomaly.quote;
            if (!quote) return;

            const newParts: typeof parts = [];
            parts.forEach(part => {
                if (part.anomaly) {
                    newParts.push(part);
                    return;
                }

                // Split by quote - use split/join pattern or regex escape
                const segments = part.text.split(quote);
                segments.forEach((segment, i) => {
                    if (segment) newParts.push({ text: segment });
                    if (i < segments.length - 1) newParts.push({ text: quote, anomaly });
                });
            });
            parts = newParts;
        });

        return (
            <div className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                {parts.map((part, i) =>
                    part.anomaly ? (
                        <span key={i} className="relative group/highlight cursor-help inline-block">
                            <span className="bg-rose-500/10 text-rose-600 dark:text-rose-400 border-b-2 border-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.2)] px-0.5 rounded-sm font-semibold">
                                {part.text}
                            </span>
                            {/* Tooltip */}
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-zinc-900 text-white text-xs rounded-xl shadow-xl opacity-0 group-hover/highlight:opacity-100 transition-opacity pointer-events-none z-50 border border-zinc-700">
                                <div className="font-bold text-rose-400 mb-1 flex items-center gap-1">
                                    <AlertCircle className="w-3 h-3" /> Suspicious Clause
                                </div>
                                <p className="mb-2 opacity-90">{part.anomaly.issue}</p>
                                <div className="bg-zinc-800 p-2 rounded-lg border border-zinc-700">
                                    <strong className="text-emerald-400 block mb-1">Suggestion:</strong>
                                    {part.anomaly.suggestion}
                                </div>
                                <div className="absolute bottom-[-6px] left-1/2 -translate-x-1/2 w-3 h-3 bg-zinc-900 rotate-45 border-b border-r border-zinc-700"></div>
                            </div>
                        </span>
                    ) : (
                        <span key={i}>{part.text}</span>
                    )
                )}
            </div>
        );
    };

    return (
        <div className="h-full flex flex-col p-6 gap-6 bg-[#F8FAFC] dark:bg-[#0B1120]">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <FileText className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                    {t.documents.title}
                </h1>
                <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">
                    {t.documents.subtitle}
                </p>
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">

                {/* Main Content Area (Upload OR Document Viewer) */}
                <div className={`transition-all duration-500 flex flex-col ${uploadState === "complete" ? "lg:col-span-7" : "lg:col-span-8 lg:col-start-3"}`}>

                    {uploadState === "complete" ? (
                        <div className="flex-1 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-500">
                            <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50">
                                <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                    <File className="w-4 h-4 text-purple-500" />
                                    Document Viewer
                                </h3>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs px-2 py-1 rounded-full bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400 border border-rose-200 dark:border-rose-900 font-medium flex items-center gap-1">
                                        <AlertCircle className="w-3 h-3" />
                                        {anomalies.length} Anomalies Detected
                                    </span>
                                    <button
                                        onClick={() => { setUploadState("idle"); setAnalyzedDoc(null); }}
                                        className="p-1 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full transition-colors"
                                    >
                                        <X className="w-5 h-5 text-slate-500" />
                                    </button>
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto p-6 bg-slate-50 dark:bg-[#0B1120] relative">
                                <div className="max-w-none prose dark:prose-invert">
                                    {renderHighlightedText(fullText, anomalies)}
                                </div>
                            </div>
                        </div>
                    ) : (
                        // Upload Zone (Original)
                        <div
                            className={`flex-1 relative rounded-2xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center p-8 text-center bg-white dark:bg-slate-900 shadow-sm ${dragActive
                                ? "border-blue-500 bg-blue-50/50 dark:bg-blue-900/10 scale-[0.99]"
                                : "border-slate-200 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-500"
                                }`}
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                        >
                            {uploadState === "idle" && (
                                <div className="space-y-4 max-w-md mx-auto pointer-events-none">
                                    <div className="w-20 h-20 mx-auto bg-purple-100 dark:bg-purple-900/30 rounded-2xl flex items-center justify-center">
                                        <Upload className="w-10 h-10 text-purple-600 dark:text-purple-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                                            {t.documents.dropFiles}
                                        </h3>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                                            {t.documents.supportedFormats}
                                        </p>
                                    </div>
                                    <button className="pointer-events-auto px-6 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-medium hover:opacity-90 transition-opacity shadow-lg shadow-purple-500/20">
                                        {t.documents.chooseFiles}
                                    </button>
                                </div>
                            )}

                            {uploadState === "uploading" && (
                                <div className="space-y-4 animate-fade-in">
                                    <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto" />
                                    <p className="font-medium text-slate-700 dark:text-slate-300">{t.documents.uploading}</p>
                                </div>
                            )}

                            {uploadState === "analyzing" && (
                                <div className="space-y-4 animate-fade-in">
                                    <Sparkles className="w-12 h-12 text-purple-500 animate-pulse mx-auto" />
                                    <div className="space-y-1">
                                        <p className="font-medium text-slate-700 dark:text-slate-300">{t.documents.analyzing}</p>
                                        <p className="text-xs text-slate-500">Scanning for legal anomalies...</p>
                                    </div>
                                </div>
                            )}

                            {uploadState === "error" && (
                                <div className="space-y-4 animate-fade-in">
                                    <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
                                    <p className="font-medium text-red-600 dark:text-red-400">Analysis Failed</p>
                                    <button
                                        onClick={() => setUploadState("idle")}
                                        className="px-4 py-2 text-sm text-slate-500 hover:text-slate-700 pointer-events-auto underline"
                                    >
                                        Try Again
                                    </button>
                                </div>
                            )}

                            {/* Overlay input for click to upload */}
                            {uploadState === "idle" && (
                                <input
                                    type="file"
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    onChange={(e) => e.target.files?.[0] && handleFiles(e.target.files[0])}
                                />
                            )}
                        </div>
                    )}
                </div>

                {/* Right Sidebar (Tabs) */}
                {analyzedDoc && (
                    <div className="lg:col-span-5 flex flex-col animate-in slide-in-from-right-10 duration-500">
                        <div className="glass-card rounded-2xl flex-1 flex flex-col overflow-hidden h-full">

                            {/* Tabs Header */}
                            <div className="flex items-center border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 p-1">
                                <button
                                    onClick={() => setActiveTab("analysis")}
                                    className={`flex-1 py-2 text-sm font-medium rounded-xl transition-all ${activeTab === "analysis"
                                        ? "bg-white dark:bg-zinc-800 text-slate-900 dark:text-white shadow-sm"
                                        : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                                        }`}
                                >
                                    Analysis
                                </button>
                                <button
                                    onClick={() => setActiveTab("chat")}
                                    className={`flex-1 py-2 text-sm font-medium rounded-xl transition-all ${activeTab === "chat"
                                        ? "bg-white dark:bg-zinc-800 text-slate-900 dark:text-white shadow-sm"
                                        : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                                        }`}
                                >
                                    Chat & AI Search
                                </button>
                            </div>

                            <div className="flex-1 p-0 overflow-hidden relative">
                                {/* Tab: Analysis */}
                                {activeTab === "analysis" && (
                                    <div className="absolute inset-0 overflow-y-auto custom-scrollbar">
                                        <div className="divide-y divide-slate-100 dark:divide-slate-800 animate-fade-in">
                                            {/* ... Existing Analysis Content ... */}
                                            <div className="p-4">
                                                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">File Name</span>
                                                <p className="text-sm font-medium text-slate-700 dark:text-slate-200 truncate" title={analyzedDoc.name}>
                                                    {analyzedDoc.name}
                                                </p>
                                                <p className="text-xs text-slate-500 mt-1">{analyzedDoc.size} • {analyzedDoc.type}</p>
                                                <p className="text-xs text-slate-500 mt-1">{analyzedDoc.date}</p>
                                            </div>

                                            <div className="p-4 bg-purple-50/50 dark:bg-purple-900/10">
                                                <span className="text-xs font-bold text-purple-600 dark:text-purple-400 uppercase tracking-wider block mb-2">Summary</span>
                                                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                                                    {analyzedDoc.summary}
                                                </p>
                                            </div>

                                            <div className="p-4">
                                                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Potential Risks</span>
                                                <div className="space-y-2">
                                                    {analyzedDoc.charges.map((charge, i) => (
                                                        <div key={i} className="flex items-start gap-2 text-sm p-3 rounded-xl bg-rose-50 dark:bg-rose-900/10 text-rose-700 dark:text-rose-300 border border-rose-100 dark:border-rose-900/30">
                                                            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                                                            <span className="leading-snug">{charge}</span>
                                                        </div>
                                                    ))}
                                                    {analyzedDoc.charges.length === 0 && <p className="text-sm text-muted-foreground">No high-level risks detected.</p>}
                                                </div>
                                            </div>
                                            <div className="p-4">
                                                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">{t.documents.parties}</span>
                                                <ul className="space-y-1">
                                                    {analyzedDoc.parties.map((party, i) => (
                                                        <li key={i} className="text-sm text-slate-600 dark:text-slate-300 flex items-center gap-2">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
                                                            {party}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Tab: Chat */}
                                {activeTab === "chat" && (
                                    <div className="absolute inset-0 flex flex-col animate-in slide-in-from-bottom-2 fade-in">
                                        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                                            {chatMessages.map((msg, i) => (
                                                <div key={i} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                                                    <div className={`max-w-[90%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.role === "user"
                                                        ? "bg-slate-900 text-white rounded-tr-none"
                                                        : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-none border border-slate-200 dark:border-slate-700"
                                                        }`}>
                                                        <p className="whitespace-pre-wrap">{msg.content}</p>
                                                    </div>

                                                    {/* Citations */}
                                                    {msg.citations && msg.citations.length > 0 && (
                                                        <div className="mt-2 w-full max-w-[90%] space-y-2">
                                                            <p className="text-[10px] uppercase font-bold text-slate-400 ml-1">Referenced Cases</p>
                                                            {msg.citations.map((cit: any, j: number) => (
                                                                <div key={j} className="bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-900/30 p-3 rounded-xl text-xs">
                                                                    <div className="font-bold text-amber-700 dark:text-amber-400 mb-1 flex items-center gap-1">
                                                                        <BookOpen className="w-3 h-3" /> {cit.title}
                                                                    </div>
                                                                    <p className="text-amber-800/80 dark:text-amber-200/70 italic line-clamp-3">"{cit.snippet}..."</p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                            {isChatLoading && (
                                                <div className="flex items-start">
                                                    <div className="bg-slate-100 dark:bg-slate-800 px-4 py-3 rounded-2xl rounded-tl-none border border-slate-200 dark:border-slate-700">
                                                        <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        <div className="p-3 bg-white dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800">
                                            <div className="flex gap-2">
                                                <input
                                                    className="flex-1 bg-slate-100 dark:bg-slate-800 border-none rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-purple-500/20 outline-none text-slate-900 dark:text-white placeholder:text-slate-400"
                                                    placeholder="Ask relevant questions..."
                                                    value={chatInput}
                                                    onChange={(e) => setChatInput(e.target.value)}
                                                    onKeyDown={(e) => e.key === "Enter" && handleChatSend()}
                                                />
                                                <button
                                                    onClick={handleChatSend}
                                                    disabled={isChatLoading || !chatInput.trim()}
                                                    className="p-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl hover:opacity-90 disabled:opacity-50 transition-opacity"
                                                >
                                                    <Send className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
