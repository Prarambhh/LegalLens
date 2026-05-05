"use client";

import { useState } from "react";
import {
    FileText,
    FileEdit,
    Copy,
    Download,
    Wand2,
    AlertTriangle,
    Scale,
    FileCheck,
    ChevronRight,
    PenTool
} from "lucide-react";
import { useLanguage } from "@/components/LanguageProvider";

const templates = [
    {
        id: "bail",
        name: "Bail Application",
        description: "Application for regular/anticipatory bail under BNSS",
        icon: Scale,
        category: "Criminal",
    },
    {
        id: "complaint",
        name: "Criminal Complaint",
        description: "Private complaint under Section 223 BNSS",
        icon: FileText,
        category: "Criminal",
    },
    {
        id: "fir-quash",
        name: "FIR Quashing Petition",
        description: "Petition under Section 528 BNSS (High Court)",
        icon: AlertTriangle,
        category: "Criminal",
    },
    {
        id: "vakalatnama",
        name: "Vakalatnama",
        description: "Authorization for legal representation",
        icon: FileCheck,
        category: "General",
    },
];

const sampleDraft = `IN THE COURT OF [COURT NAME]
AT [LOCATION]

CRIMINAL MISC. APPLICATION NO. _____ OF 2024

IN THE MATTER OF:

[APPLICANT NAME]                                    ... APPLICANT
    S/o [FATHER'S NAME]
    R/o [ADDRESS]

VERSUS

STATE OF [STATE]                                    ... RESPONDENT

APPLICATION FOR REGULAR BAIL UNDER SECTION 483 OF
BHARATIYA NAGARIK SURAKSHA SANHITA, 2023

MOST RESPECTFULLY SHOWETH:

1. That the applicant has been arrested on [DATE] in connection with FIR No. [FIR NUMBER] registered at Police Station [PS NAME] under Sections [SECTIONS] of the Bharatiya Nyaya Sanhita, 2023.

2. That the applicant is falsely implicated in the present case and has nothing to do with the alleged offence.

3. That the investigation in the matter is complete and the applicant is no longer required for any investigation purpose.

4. That the applicant is ready to abide by any conditions that this Hon'ble Court may deem fit to impose.

PRAYER:

In view of the above facts and circumstances, it is most respectfully prayed that this Hon'ble Court may be pleased to:

a) Grant regular bail to the applicant in connection with the aforementioned FIR.

b) Pass any other order as this Hon'ble Court may deem fit and proper in the facts and circumstances of the case.

AND FOR THIS ACT OF KINDNESS, THE APPLICANT SHALL EVER PRAY.

                                                    APPLICANT
                                            THROUGH COUNSEL

PLACE: [LOCATION]
DATE: [DATE]`;

export default function DraftingPage() {
    const { t } = useLanguage();
    const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
    const [draftContent, setDraftContent] = useState("");
    const [isGenerating, setIsGenerating] = useState(false);

    const handleGenerateDraft = async () => {
        setIsGenerating(true);
        try {
            const template = templates.find(t => t.id === selectedTemplate);
            const templateName = template?.name || "Legal Document";
            const templateDesc = template?.description || "";

            const prompt = `Draft a professional ${templateName} (${templateDesc}) for use in Indian Courts. 
Include placeholders like [CLIENT NAME], [DATE], etc. where appropriate. 
Ensure it complies with the latest laws (BNS/BNSS).`;

            const response = await fetch("http://127.0.0.1:8000/api/chat/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: prompt,
                    act_filter: null,
                    top_k: 3 // Retrieve getting few format references is good
                })
            });

            if (!response.ok) throw new Error("Generation failed");

            const data = await response.json();
            setDraftContent(data.answer);
        } catch (error) {
            console.error(error);
            setDraftContent("Error generating draft. Please check backend connection.");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(draftContent);
    };

    const handleDownload = () => {
        const blob = new Blob([draftContent], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${selectedTemplate || "draft"}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="h-full flex flex-col relative overflow-hidden">
            {/* Ambient Background */}
            <div className="absolute inset-0 pointer-events-none z-0">
                <div className="absolute top-[-5%] left-[20%] w-[500px] h-[500px] bg-orange-500/5 dark:bg-orange-500/10 rounded-full blur-[100px]" />
            </div>

            {/* Header */}
            <header className="bg-background/80 border-b border-border p-6 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-br from-orange-500 to-amber-600 rounded-xl shadow-lg shadow-orange-500/20 text-white">
                        <PenTool className="w-6 h-6" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold font-heading">{t.drafting.title}</h1>
                        <p className="text-sm text-muted-foreground">
                            {t.drafting.subtitle}
                        </p>
                    </div>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden relative z-10">
                {/* Template Selector */}
                <aside className="w-80 bg-card/50 border-r border-border overflow-y-auto backdrop-blur-sm">
                    <div className="p-4">
                        <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 px-2">
                            {t.drafting.templates}
                        </h3>
                        <div className="space-y-2">
                            {templates.map((template) => {
                                const Icon = template.icon;
                                return (
                                    <button
                                        key={template.id}
                                        onClick={() => setSelectedTemplate(template.id)}
                                        className={`w-full text-left p-3 rounded-xl transition-all border group ${selectedTemplate === template.id
                                            ? "bg-primary/10 border-primary/20 shadow-sm"
                                            : "bg-transparent border-transparent hover:bg-card hover:border-border"
                                            }`}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors ${selectedTemplate === template.id
                                                ? "bg-primary text-primary-foreground"
                                                : "bg-muted text-muted-foreground group-hover:text-foreground"
                                                }`}>
                                                <Icon className="w-4 h-4" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className={`font-semibold text-sm truncate ${selectedTemplate === template.id ? 'text-primary' : 'text-foreground'}`}>
                                                    {template.name}
                                                </p>
                                                <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                                                    {template.description}
                                                </p>
                                            </div>
                                            {selectedTemplate === template.id && (
                                                <ChevronRight className="w-4 h-4 text-primary mt-1" />
                                            )}
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                </aside>

                {/* Main Editor */}
                <main className="flex-1 flex flex-col p-6 overflow-hidden">
                    {!selectedTemplate ? (
                        <div className="flex-1 flex items-center justify-center">
                            <div className="text-center max-w-sm p-8 rounded-2xl border-2 border-dashed border-border/50 bg-card/30">
                                <div className="w-16 h-16 mx-auto rounded-2xl bg-muted/50 flex items-center justify-center mb-4 text-muted-foreground">
                                    <FileEdit className="w-8 h-8" />
                                </div>
                                <h2 className="text-lg font-semibold mb-2">
                                    {t.drafting.selectTemplate}
                                </h2>
                                <p className="text-muted-foreground text-sm">
                                    {t.drafting.selectTemplateDesc}
                                </p>
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col bg-card rounded-2xl shadow-xl border border-border overflow-hidden animate-in fade-in zoom-in-95 duration-300">
                            {/* Toolbar */}
                            <div className="p-4 border-b border-border flex items-center justify-between bg-muted/30">
                                <div className="flex items-center gap-3">
                                    <h2 className="font-semibold text-foreground">
                                        {templates.find(t => t.id === selectedTemplate)?.name}
                                    </h2>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={handleGenerateDraft}
                                        disabled={isGenerating}
                                        className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:opacity-90 disabled:opacity-70 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/40 active:scale-95"
                                    >
                                        <Wand2 className={`w-4 h-4 ${isGenerating ? "animate-spin" : ""}`} />
                                        {isGenerating ? t.drafting.generating : t.drafting.generateDraft}
                                    </button>

                                    {draftContent && (
                                        <>
                                            <div className="w-px h-6 bg-border mx-1" />
                                            <button
                                                onClick={handleCopy}
                                                className="p-2 text-muted-foreground hover:bg-muted hover:text-foreground rounded-lg transition-colors"
                                                title={t.drafting.copy}
                                            >
                                                <Copy className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={handleDownload}
                                                className="p-2 text-muted-foreground hover:bg-muted hover:text-foreground rounded-lg transition-colors"
                                                title={t.drafting.download}
                                            >
                                                <Download className="w-4 h-4" />
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>

                            {/* Editor Area */}
                            <div className="flex-1 relative">
                                <textarea
                                    value={draftContent}
                                    onChange={(e) => setDraftContent(e.target.value)}
                                    placeholder={t.drafting.placeholder}
                                    className="w-full h-full p-8 bg-transparent text-foreground font-mono text-sm resize-none focus:outline-none leading-relaxed placeholder:text-muted-foreground/50"
                                    spellCheck={false}
                                />
                                {!draftContent && !isGenerating && (
                                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                        <p className="text-muted-foreground/50 text-sm max-w-xs text-center">
                                            Generate a draft to see the content here. You can then edit it manually.
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
