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
  title: "Prospera — Autonomous Wealth Systems",
  description:
    "Governed strategy bots trading deterministic five-minute rounds against live markets — trade-only permissions, server-verified settlement, and a live watch-only demo desk.",
  keywords: ["wealth automation", "trading bots", "capital deployment", "crypto bots", "gold", "quant engine"],
  openGraph: {
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

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable} ${serif.variable}`}>
      <body>{children}</body>
    </html>
  );
}
