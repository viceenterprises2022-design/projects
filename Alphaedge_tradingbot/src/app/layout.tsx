import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono, Instrument_Serif } from "next/font/google";
import "./globals.css";

const sans = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const mono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

const serif = Instrument_Serif({
  weight: "400",
  subsets: ["latin"],
  style: ["normal", "italic"],
  variable: "--font-serif",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://www.alphaedgeai.io"),
  title: "Prospera — Autonomous Wealth Systems",
  description:
    "Governed strategy bots trading deterministic five-minute rounds against live markets — trade-only permissions, server-verified settlement, and a live watch-only demo desk.",
  keywords: ["wealth automation", "trading bots", "capital deployment", "crypto bots", "gold", "quant engine"],
  openGraph: {
    url: "https://www.alphaedgeai.io",
    title: "Prospera — Autonomous Wealth Systems",
    description:
      "Watch a live quant desk trade XAU, BTC, and ETH in verifiable five-minute rounds. Trade-only permissions, server-verified settlement.",
    siteName: "Prospera",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Prospera — Autonomous Wealth Systems",
    description:
      "Watch a live quant desk trade XAU, BTC, and ETH in verifiable five-minute rounds.",
  },
};

export const viewport = {
  themeColor: "#050711",
};

// Applied before first paint so a light-mode user never sees a dark flash.
// Dark is the default and the fallback if storage is unavailable.
const THEME_INIT = `(function(){try{var t=localStorage.getItem('prospera-theme');document.documentElement.setAttribute('data-theme',t==='light'?'light':'dark');}catch(e){document.documentElement.setAttribute('data-theme','dark');}})();`;

export default function RootLayout({ children }: { children: ReactNode }) {
  // suppressHydrationWarning: THEME_INIT deliberately rewrites data-theme
  // before React hydrates, so the server value ("dark") and the client value
  // legitimately differ for a light-mode reader. This is the documented
  // escape hatch for pre-paint theme stamping.
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning className={`${sans.variable} ${mono.variable} ${serif.variable}`}>
      <head><script dangerouslySetInnerHTML={{ __html: THEME_INIT }} /></head>
      <body>{children}</body>
    </html>
  );
}
