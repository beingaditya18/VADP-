import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "VADP | Zero Trust Explainable AI for Judicial Decision Support",
  description:
    "A research framework combining Zero Trust Architecture, Explainable AI, Retrieval-Augmented Generation, and tamper-evident audit ledger for secure judicial decision support.",
  keywords: [
    "judicial AI",
    "zero trust",
    "explainable AI",
    "SHAP",
    "RAG",
    "legal tech",
    "audit ledger",
  ],
  authors: [{ name: "VADP Authors" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} dark`} suppressHydrationWarning>
      <body className="min-h-screen bg-[#0a0a0f] text-white font-[family-name:var(--font-inter)] antialiased">
        {children}
      </body>
    </html>
  );
}
