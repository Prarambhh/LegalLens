"use client";

import { useLanguage } from "@/components/LanguageProvider";
import { Scale, ArrowRight, Zap, Shield, Sparkles, Search, GitCompare, Layout } from "lucide-react";
import Link from "next/link";
import { useTheme } from "@/components/ThemeProvider";

export default function Home() {
  const { t } = useLanguage();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 md:p-12 space-y-16 relative overflow-hidden">

      {/* Background Ambience */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-orange-500/10 dark:bg-orange-500/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-amber-500/10 dark:bg-amber-500/20 rounded-full blur-[100px]" />
      </div>

      {/* Hero Section */}
      <section className="text-center space-y-8 max-w-5xl relative z-10">

        {/* Logo/Header for Home Page only */}
        <div className="absolute top-0 left-0 right-0 -mt-8 flex justify-between items-center w-full px-4 md:px-0">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-tr from-orange-500 to-amber-500 rounded-xl flex items-center justify-center text-white shadow-lg shadow-orange-500/20">
              <Scale className="w-6 h-6" />
            </div>
            <span className="text-xl font-bold font-heading tracking-tight">LegalLens</span>
          </div>

          <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-muted transition-colors">
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>


        <div className="inline-flex items-center gap-2 px-4 py-2 mt-20 rounded-full bg-white/50 dark:bg-white/10 border border-orange-500/20 backdrop-blur-md shadow-lg animate-float">
          <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
          <span className="text-sm font-medium text-orange-600 dark:text-orange-400">
            Now Live: BNS 2023 Support
          </span>
        </div>

        <h1 className="text-6xl md:text-8xl font-bold font-heading tracking-tighter text-foreground leading-[0.9]">
          The Future of <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-orange-600 via-amber-500 to-orange-600 animate-gradient-x bg-[length:200%_auto]">Legal Intelligence.</span>
        </h1>

        <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto font-light leading-relaxed">
          {t.app.welcomeSubtitle}
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link href="/research" className="group relative px-8 py-4 bg-orange-600 text-white rounded-full font-bold text-lg hover:shadow-2xl hover:shadow-orange-500/40 transition-all active:scale-95">
            <span className="relative z-10 flex items-center gap-2">
              Start Researching <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </span>
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-orange-600 to-amber-600 opacity-0 group-hover:opacity-100 transition-opacity blur-lg -z-10" />
          </Link>
          <Link href="/compare" className="px-8 py-4 bg-white/50 dark:bg-white/10 border border-border hover:border-orange-500/50 rounded-full font-semibold text-lg hover:bg-orange-500/5 transition-all backdrop-blur-sm">
            Compare Laws
          </Link>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full max-w-7xl relative z-10">
        {[
          {
            title: t.home.legalResearch,
            desc: t.home.legalResearchDesc,
            icon: Search,
            href: "/research",
            color: "text-orange-500",
            bg: "bg-orange-500/10",
            hover: "group-hover:text-orange-600"
          },
          {
            title: t.home.compareLaws,
            desc: t.home.compareLawsDesc,
            icon: GitCompare,
            href: "/compare",
            color: "text-amber-500",
            bg: "bg-amber-500/10",
            hover: "group-hover:text-amber-600"
          },
          {
            title: t.home.draftDocuments,
            desc: t.home.draftDocumentsDesc,
            icon: Sparkles,
            href: "/drafting",
            color: "text-red-500",
            bg: "bg-red-500/10",
            hover: "group-hover:text-red-600"
          },
          {
            title: t.home.analyzeDocuments,
            desc: t.home.analyzeDocumentsDesc,
            icon: Shield,
            href: "/documents",
            color: "text-orange-400",
            bg: "bg-orange-400/10",
            hover: "group-hover:text-orange-500"
          }
        ].map((feature, i) => (
          <Link
            key={i}
            href={feature.href}
            className="modern-card modern-card-hover p-6 rounded-3xl group flex flex-col justify-between h-[280px] hover:border-orange-500/30"
          >
            <div className={`w-14 h-14 rounded-2xl ${feature.bg} flex items-center justify-center mb-6 transition-colors`}>
              <feature.icon className={`w-7 h-7 ${feature.color}`} />
            </div>

            <div>
              <h3 className={`text-xl font-bold font-heading mb-2 transition-colors ${feature.hover}`}>
                {feature.title}
              </h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {feature.desc}
              </p>
            </div>

            <div className={`mt-6 flex items-center text-sm font-semibold text-foreground/80 transition-colors ${feature.hover}`}>
              Explore <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        ))}
      </section>

    </div>
  );
}
