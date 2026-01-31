"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import en from "@/i18n/en.json";
import hi from "@/i18n/hi.json";
import ta from "@/i18n/ta.json";
import te from "@/i18n/te.json";
import bn from "@/i18n/bn.json";
import mr from "@/i18n/mr.json";
import gu from "@/i18n/gu.json";

export type Language = "en" | "hi" | "ta" | "te" | "bn" | "mr" | "gu";

type TranslationsType = typeof en;

interface LanguageContextType {
    language: Language;
    setLanguage: (lang: Language) => void;
    t: TranslationsType;
}

const translations: Record<Language, TranslationsType> = {
    en,
    hi,
    ta,
    te,
    bn,
    mr,
    gu,
};

const languageNames: Record<Language, string> = {
    en: "English",
    hi: "हिंदी",
    ta: "தமிழ்",
    te: "తెలుగు",
    bn: "বাংলা",
    mr: "मराठी",
    gu: "ગુજરાતી",
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
    const [language, setLanguageState] = useState<Language>("en");

    useEffect(() => {
        // Check localStorage for saved language preference
        const stored = localStorage.getItem("language") as Language | null;
        if (stored && translations[stored]) {
            setLanguageState(stored);
        }
    }, []);

    const setLanguage = (lang: Language) => {
        setLanguageState(lang);
        localStorage.setItem("language", lang);
        // Update HTML lang attribute
        document.documentElement.lang = lang;
    };

    return (
        <LanguageContext.Provider
            value={{
                language,
                setLanguage,
                t: translations[language]
            }}
        >
            {children}
        </LanguageContext.Provider>
    );
}

export function useLanguage(): LanguageContextType {
    const context = useContext(LanguageContext);
    if (!context) {
        // Return defaults if outside provider
        return {
            language: "en",
            setLanguage: () => { },
            t: en,
        };
    }
    return context;
}

export { languageNames };
