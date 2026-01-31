"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Scale,
  Search,
  GitCompare,
  FileText,
  FolderOpen,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  Globe,
} from "lucide-react";
import { useState } from "react";
import { useTheme } from "./ThemeProvider";
import { useLanguage, languageNames, Language } from "./LanguageProvider";

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [showLangMenu, setShowLangMenu] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();

  if (pathname === "/") {
    return null;
  }

  const navItems = [
    { name: t.nav.research, href: "/research", icon: Search },
    { name: t.nav.compareLaws, href: "/compare", icon: GitCompare },
    { name: t.nav.drafting, href: "/drafting", icon: FileText },
    { name: t.nav.documents, href: "/documents", icon: FolderOpen },
  ];

  return (
    <aside
      className={`relative z-50 h-screen transition-all duration-500 ease-out border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 ${collapsed ? "w-20" : "w-72"
        }`}
    >
      <div className="flex flex-col h-full p-4">
        {/* Brand */}
        <div className={`flex items-center gap-3 mb-6 ${collapsed ? "justify-center" : "px-2"}`}>
          <div className="relative group">
            <div className="absolute inset-0 bg-gradient-to-tr from-orange-500 to-amber-500 rounded-xl blur-lg opacity-20 group-hover:opacity-40 transition-opacity" />
            <div className="relative w-10 h-10 bg-gradient-to-tr from-orange-500 to-amber-500 rounded-xl flex items-center justify-center text-white shadow-md">
              <Scale className="w-5 h-5" />
            </div>
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <h1 className="text-lg font-bold font-heading tracking-tight text-zinc-900 dark:text-zinc-100">LegalLens</h1>
              <span className="text-[10px] uppercase tracking-widest text-zinc-500 dark:text-zinc-500 font-semibold">AI Legal Suite</span>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 relative overflow-hidden ${isActive
                  ? "bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400 font-semibold"
                  : "text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-200"
                  }`}
              >
                <Icon className={`w-5 h-5 relative z-10 transition-transform duration-300 ${isActive ? "" : "group-hover:scale-110"}`} />

                {!collapsed && (
                  <span className="text-sm relative z-10">{item.name}</span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer Actions */}
        <div className="mt-auto space-y-2 pt-4 border-t border-zinc-200 dark:border-zinc-800">
          {/* Language Toggle */}
          <div className="relative">
            <button
              onClick={() => setShowLangMenu(!showLangMenu)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${collapsed ? "justify-center" : ""
                } hover:bg-zinc-100 dark:hover:bg-zinc-900 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200`}
            >
              <Globe className="w-4 h-4" />
              {!collapsed && (
                <span className="text-sm font-medium">{languageNames[language]}</span>
              )}
            </button>

            {showLangMenu && (
              <div className={`absolute bottom-full left-0 mb-2 w-full min-w-[200px] bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xl rounded-xl p-2 z-50 overflow-hidden animate-in slide-in-from-bottom-2 fade-in ${collapsed ? "left-full ml-4" : ""}`}>
                <div className="max-h-60 overflow-y-auto space-y-1 custom-scrollbar">
                  {(Object.keys(languageNames) as Language[]).map((lang) => (
                    <button
                      key={lang}
                      onClick={() => {
                        setLanguage(lang);
                        setShowLangMenu(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${language === lang
                        ? "bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400 font-semibold"
                        : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                        }`}
                    >
                      {languageNames[lang]}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${collapsed ? "justify-center" : ""
              } hover:bg-zinc-100 dark:hover:bg-zinc-900 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200`}
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            {!collapsed && (
              <span className="text-sm font-medium">
                {theme === "dark" ? t.nav.lightMode : t.nav.darkMode}
              </span>
            )}
          </button>

          {/* Collapse Toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex items-center justify-center w-full py-2 text-zinc-400 dark:text-zinc-600 hover:text-orange-500 transition-colors"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </aside>
  );
}
