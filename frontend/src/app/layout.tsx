import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Sidebar } from "@/components/Sidebar";
import { LanguageProvider } from "@/components/LanguageProvider";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata = {
  title: "LegalLens | AI Legal Assistant",
  description: "Advanced AI legal assistant for Indian Law (IPC/BNS)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className={`${inter.variable} ${outfit.variable}`}>
      <body className="font-sans antialiased selection:bg-primary/30 selection:text-primary">
        <LanguageProvider>
          <ThemeProvider>
            <div className="flex h-screen overflow-hidden bg-background">
              <Sidebar />
              <main className="flex-1 overflow-auto relative">
                {/* Global Background Effect */}
                {/* Global Background Effect - Optimized for Professional Look */}
                <div className="fixed inset-0 z-[-1] pointer-events-none">
                  {/* Light Mode: Subtle Warmth */}
                  <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-orange-100/40 rounded-full blur-[100px] dark:hidden mix-blend-multiply" />

                  {/* Dark Mode: Deep Glow */}
                  <div className="hidden dark:block absolute top-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-primary/10 blur-[120px] mix-blend-screen animate-pulse" />
                  <div className="hidden dark:block absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] rounded-full bg-blue-500/10 blur-[100px] mix-blend-screen" />
                </div>
                {children}
              </main>
            </div>
          </ThemeProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
