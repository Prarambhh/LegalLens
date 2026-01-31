"use client";

import { useState } from "react";
import { ArrowRightLeft, Search, FileText, ChevronRight } from "lucide-react";
import { useLanguage } from "@/components/LanguageProvider";

type LawSection = {
    id: string;
    act: string;
    section: string;
    title: string;
    content: string;
};

type Mapping = {
    oldSectionId: string;
    newSectionId: string;
    changeType: "added" | "removed" | "modified" | "unchanged";
    summary: string;
    diff?: {
        added: string[];
        removed: string[];
    };
};

// Mock Data Removed - Using Backend API

export default function ComparePage() {
    const { t } = useLanguage();
    const [searchQuery, setSearchQuery] = useState("");
    const [result, setResult] = useState<{ old: LawSection, new: LawSection, mapping: Mapping } | null>(null);
    const [notFound, setNotFound] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const handleAnalyze = async () => {
        if (!searchQuery.trim()) return;

        setIsLoading(true);
        setNotFound(false);
        setResult(null);

        try {
            const response = await fetch("http://localhost:8000/api/compare/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: searchQuery })
            });

            if (!response.ok) {
                if (response.status === 404) {
                    setNotFound(true);
                } else {
                    console.error("Comparison failed");
                }
                return;
            }

            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error("Comparison error:", error);
            // Optionally set error state
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="h-full flex flex-col p-4 lg:p-6 max-w-[1600px] mx-auto space-y-6 relative overflow-hidden">
            {/* Ambient Background */}
            <div className="absolute inset-0 pointer-events-none z-0">
                <div className="absolute top-[-10%] right-[10%] w-[400px] h-[400px] bg-orange-500/5 dark:bg-orange-500/10 rounded-full blur-[100px]" />
            </div>

            {/* Header */}
            <header className="flex items-center justify-between relative z-10 border-b border-border/50 pb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary">
                        <ArrowRightLeft className="w-5 h-5" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold font-heading tracking-tight">{t.compare.title}</h1>
                        <p className="text-xs text-muted-foreground">{t.compare.subtitle}</p>
                    </div>
                </div>

                {/* Compact Search */}
                <div className="relative w-full max-w-md">
                    <div className="relative bg-card border border-border rounded-lg flex items-center p-1 shadow-sm">
                        <Search className="w-4 h-4 text-muted-foreground ml-3" />
                        <input
                            type="text"
                            placeholder="Search (e.g. IPC 420)..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                            className="w-full bg-transparent border-none focus:ring-0 text-sm px-3 py-1.5 placeholder:text-muted-foreground/50 text-foreground"
                        />
                        <button
                            onClick={handleAnalyze}
                            disabled={isLoading}
                            className="px-4 py-1.5 bg-primary text-primary-foreground text-xs font-semibold rounded-md hover:opacity-90 transition-all shadow-sm disabled:opacity-70"
                        >
                            {isLoading ? "Analyzing..." : "Analyze"}
                        </button>
                    </div>
                </div>
            </header>

            {/* Split View */}
            <div className="flex-1 min-h-0 relative z-10">
                {notFound ? (
                    <div className="flex flex-col items-center justify-center h-64 text-center space-y-4">
                        <div className="p-4 bg-muted/50 rounded-full">
                            <Search className="w-8 h-8 text-muted-foreground" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-foreground">Section unavailable</h3>
                            <p className="text-sm text-muted-foreground">Try sections 420, 302, 376, or 124A.</p>
                        </div>
                    </div>
                ) : result && (
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-full">
                        {/* Left: Old Law */}
                        <div className="lg:col-span-4 flex flex-col bg-card rounded-xl overflow-hidden border border-border shadow-sm">
                            <div className="p-3 bg-muted/30 border-b border-border flex items-center justify-between">
                                <span className="font-semibold text-sm text-muted-foreground flex items-center gap-2">
                                    <FileText className="w-4 h-4" /> IPC 1860
                                </span>
                                <span className="px-1.5 py-0.5 rounded bg-destructive/10 text-destructive text-[10px] font-bold uppercase tracking-wider">
                                    {t.compare.repealed}
                                </span>
                            </div>
                            <div className="p-4 overflow-y-auto custom-scrollbar flex-1 relative">
                                <h3 className="text-lg font-bold font-heading mb-2 text-foreground/90">
                                    §{result.old.section}
                                </h3>
                                <p className="text-sm leading-relaxed text-muted-foreground font-serif">
                                    {result.old.content}
                                </p>
                            </div>
                        </div>

                        {/* Center: Transformation Logic */}
                        <div className="lg:col-span-4 flex flex-col gap-4">
                            <div className="flex items-center justify-center">
                                <div className="bg-primary/5 text-primary px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 border border-primary/10">
                                    <ArrowRightLeft className="w-3 h-3" />
                                    Mapped to BNS
                                </div>
                            </div>

                            <div className="bg-card p-4 rounded-xl border-l-4 border-l-yellow-500 bg-yellow-500/5 shadow-sm flex-1">
                                <h4 className="font-bold text-yellow-600 dark:text-yellow-400 mb-2 uppercase text-[10px] tracking-wider">
                                    Change Analysis
                                </h4>
                                <p className="text-sm font-medium leading-relaxed mb-4 text-foreground">
                                    {result.mapping.summary}
                                </p>

                                <div className="space-y-2">
                                    {result.mapping.diff?.removed.map((item, i) => (
                                        <div key={i} className="flex gap-2 text-xs">
                                            <span className="w-4 h-4 rounded-full bg-destructive/10 text-destructive flex items-center justify-center flex-shrink-0 font-bold">-</span>
                                            <span className="text-destructive line-through decoration-destructive/50 opacity-80">{item}</span>
                                        </div>
                                    ))}
                                    {result.mapping.diff?.added.map((item, i) => (
                                        <div key={i} className="flex gap-2 text-xs">
                                            <span className="w-4 h-4 rounded-full bg-green-500/10 text-green-600 flex items-center justify-center flex-shrink-0 font-bold">+</span>
                                            <span className="text-green-600 font-medium">{item}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Right: New Law */}
                        <div className="lg:col-span-4 flex flex-col bg-card rounded-xl overflow-hidden border border-primary/20 shadow-sm">
                            <div className="p-3 bg-primary/5 border-b border-primary/10 flex items-center justify-between">
                                <span className="font-semibold text-sm text-primary flex items-center gap-2">
                                    <FileText className="w-4 h-4" /> BNS 2023
                                </span>
                                <span className="px-1.5 py-0.5 rounded bg-green-500/10 text-green-600 text-[10px] font-bold uppercase tracking-wider">
                                    {t.compare.inForce}
                                </span>
                            </div>
                            <div className="p-4 overflow-y-auto custom-scrollbar flex-1 relative bg-gradient-to-b from-primary/5 to-transparent">
                                <h3 className="text-lg font-bold font-heading mb-2 text-primary">
                                    §{result.new.section}
                                </h3>
                                <p className="text-sm leading-relaxed text-foreground font-serif">
                                    {result.new.content}
                                </p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
