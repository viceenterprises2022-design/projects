"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

// The hero visual is a real window into the product: live Hyperliquid marks
// (same public feed the desk uses) and the actual 5-minute round clock —
// deterministic epoch math, identical to the canonical engine's clock.

const ASSETS = [
  { key: "XAU", label: "XAU · GOLD", sub: "PAXG PROXY" },
  { key: "BTC-PERP", label: "BTC · PERP", sub: "HYPERLIQUID" },
  { key: "ETH-PERP", label: "ETH · PERP", sub: "HYPERLIQUID" },
] as const;

function fmtUsd(n: number | undefined) {
  if (n === undefined || !Number.isFinite(n)) return "— — —";
  return "$" + n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function LiveDesk() {
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [contexts, setContexts] = useState<Record<string, { change24hPct: number }>>({});
  const [tickDir, setTickDir] = useState<Record<string, "up" | "down" | null>>({});
  const [live, setLive] = useState(false);
  const ROUND_S = 300; // 5-minute rounds — same epoch math as the engine
  const [roundSec, setRoundSec] = useState(ROUND_S - Math.floor((Date.now() / 1000) % ROUND_S));
  const prevRef = useRef<Record<string, number>>({});

  useEffect(() => {
    let cancelled = false;

    async function sync() {
      try {
        const res = await fetch("/api/dashboard/prices");
        const json = await res.json();
        if (cancelled || !json?.success) return;
        const dirs: Record<string, "up" | "down" | null> = {};
        for (const k of Object.keys(json.prices)) {
          const prev = prevRef.current[k];
          if (prev !== undefined && json.prices[k] !== prev) dirs[k] = json.prices[k] > prev ? "up" : "down";
        }
        prevRef.current = json.prices;
        setPrices(json.prices);
        setContexts(json.contexts || {});
        setLive(true);
        if (Object.keys(dirs).length) {
          setTickDir(dirs);
          setTimeout(() => { if (!cancelled) setTickDir({}); }, 750);
        }
      } catch {
        if (!cancelled) setLive(false);
      }
    }

    sync();
    const feed = setInterval(sync, 3000);
    const clock = setInterval(() => setRoundSec(ROUND_S - Math.floor((Date.now() / 1000) % ROUND_S)), 1000);
    const onVisible = () => { if (document.visibilityState === "visible") sync(); };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      clearInterval(feed);
      clearInterval(clock);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  return (
    <div className="l-desk l-rise l-d3" aria-label="Live Prospera desk preview">
      <div className="l-desk-head">
        <span className={`l-led ${live ? "ok" : "warm"}`}>
          {live ? "HYPERLIQUID FEED · LIVE" : "FEED SYNCING…"}
        </span>
        <span className="l-kicker">PROSPERA DESK</span>
      </div>

      <div className="l-desk-rows">
        {ASSETS.map(a => {
          const ctx = contexts[a.key];
          const dir = tickDir[a.key];
          return (
            <div className="l-asset" key={a.key}>
              <div className="l-asset-name">
                {a.label}
                <small>{a.sub}</small>
              </div>
              <div className={`l-asset-price ${dir === "up" ? "l-tick-up" : dir === "down" ? "l-tick-down" : ""}`}>
                {fmtUsd(prices[a.key])}
              </div>
              <div className={`l-asset-delta ${ctx ? (ctx.change24hPct >= 0 ? "l-pos" : "l-neg") : "l-dim-t"}`}>
                {ctx ? `${ctx.change24hPct >= 0 ? "▲" : "▼"} ${Math.abs(ctx.change24hPct).toFixed(2)}%` : "24H —"}
              </div>
            </div>
          );
        })}
      </div>

      <div className="l-desk-foot">
        <div className="l-round">
          <strong>{`${String(Math.floor(roundSec / 60)).padStart(2, "0")}:${String(roundSec % 60).padStart(2, "0")}`}</strong>
          <span>to next round settlement — same clock as the live engine</span>
        </div>
        <Link href="/dashboard" className="l-desk-cta">
          Watch the live desk →
        </Link>
      </div>

      <p className="l-desk-note">
        Real marks from Hyperliquid L1 · 5-minute binary rounds · server-verified settlement · watch-only demo, access by invitation
      </p>
    </div>
  );
}
