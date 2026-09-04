"use client"

import { Fragment, useCallback, useEffect, useRef, useState } from "react"
import Link from "next/link"
import ThemeToggle from "../ThemeToggle"
import { signOutFromLive } from "./live-actions"

// ---------------------------------------------------------------------------
// /live — read-only window on the canonical engine for invited viewers.
//
// It renders the same numbers the desk does but exposes no controls: every
// mutating endpoint is owner-gated server-side anyway, so this page simply
// never asks for one. Two independent polls:
//   /api/dashboard/prices — public Hyperliquid marks, 3s
//   /api/engine/state     — viewer-gated engine snapshot, 5s (also ticks it)
// ---------------------------------------------------------------------------

const ASSETS = [
  { key: "XAU", label: "XAU · GOLD", sub: "PAXG PROXY" },
  { key: "BTC-PERP", label: "BTC · PERP", sub: "HYPERLIQUID" },
  { key: "ETH-PERP", label: "ETH · PERP", sub: "HYPERLIQUID" },
] as const

interface AssetContext {
  change24hPct: number
  fundingRate: number
  openInterest: number
  dayVolumeUsd: number
}

interface LevelState {
  level: number
  label: string
  pnl: number
  wins: number
  losses: number
  bankroll: number | null
  tradesToday: number
  dailyTrades: number | null
  pnlToday: number
  dailyStopActive: boolean
  profitLockActive: boolean
  uncapped: boolean
}

interface Round {
  id: string
  asset: string
  epoch: number
  startedAt: number
  expiresAt: number
  strikePrice: number
  status: string
  side: string | null
  size: number | null
  entryPrice: number | null
  skipReason: string | null
  settledAt: number | null
}

interface EngineState {
  now: number
  roundEndsAt: number
  bankroll: number
  bankrollBase: number
  levels: LevelState[]
  regime: { mode: string; reason: string; source: string; until: number | null }
  quotaResetAt: number
  assetEnabled: Record<string, boolean>
  marks: Record<string, number>
  rounds: Round[]
  errors?: string[]
}

function fmtUsd(n: number | undefined | null, dp = 2) {
  if (n === undefined || n === null || !Number.isFinite(n)) return "— — —"
  return "$" + n.toLocaleString(undefined, { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

// Signed money with a true minus sign. Kept separate from fmtUsd so the sign
// is derived from the number rather than sliced off a formatted string, which
// silently mangles the non-finite placeholder.
function fmtSignedUsd(n: number | undefined | null, dp = 2) {
  if (n === undefined || n === null || !Number.isFinite(n)) return "— — —"
  const sign = n < 0 ? "−" : "+"
  return sign + "$" + Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: dp, maximumFractionDigits: dp })
}

function fmtCompact(n: number | undefined) {
  if (n === undefined || !Number.isFinite(n)) return "—"
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(2) + "B"
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(2) + "M"
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + "K"
  return n.toFixed(2)
}

function fmtClock(ms: number) {
  if (!Number.isFinite(ms) || ms < 0) return "00:00"
  const s = Math.floor(ms / 1000)
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`
}

function fmtTime(ms: number | null) {
  if (!ms) return "—"
  return new Date(ms).toISOString().slice(11, 19) + "Z"
}

export default function LiveClient({
  user,
  isOwner,
}: {
  user: { name?: string | null; email?: string | null }
  isOwner: boolean
}) {
  const [prices, setPrices] = useState<Record<string, number>>({})
  const [contexts, setContexts] = useState<Record<string, AssetContext>>({})
  const [tickDir, setTickDir] = useState<Record<string, "up" | "down" | null>>({})
  const [feedLive, setFeedLive] = useState(false)
  const [engine, setEngine] = useState<EngineState | null>(null)
  const [engineError, setEngineError] = useState<string | null>(null)
  // null until mounted: both derive from Date.now(), which must not run during
  // server render or the markup mismatches on hydration.
  const [nowMs, setNowMs] = useState<number | null>(null)
  const prevRef = useRef<Record<string, number>>({})

  const syncPrices = useCallback(async (signal: AbortSignal) => {
    try {
      const res = await fetch("/api/dashboard/prices", { signal, cache: "no-store" })
      const json = await res.json()
      if (signal.aborted || !json?.success) return
      const dirs: Record<string, "up" | "down" | null> = {}
      for (const k of Object.keys(json.prices)) {
        const prev = prevRef.current[k]
        if (prev !== undefined && json.prices[k] !== prev) dirs[k] = json.prices[k] > prev ? "up" : "down"
      }
      prevRef.current = json.prices
      setPrices(json.prices)
      setContexts(json.contexts || {})
      setFeedLive(true)
      if (Object.keys(dirs).length) {
        setTickDir(dirs)
        setTimeout(() => { if (!signal.aborted) setTickDir({}) }, 750)
      }
    } catch {
      if (!signal.aborted) setFeedLive(false)
    }
  }, [])

  const syncEngine = useCallback(async (signal: AbortSignal) => {
    try {
      const res = await fetch("/api/engine/state", { signal, cache: "no-store" })
      const json = await res.json()
      if (signal.aborted) return
      if (!json?.success) {
        setEngineError(json?.error || "Engine state unavailable")
        return
      }
      setEngine(json as EngineState)
      setEngineError(null)
    } catch {
      if (!signal.aborted) setEngineError("Engine unreachable — retrying")
    }
  }, [])

  useEffect(() => {
    const ac = new AbortController()
    const { signal } = ac

    syncPrices(signal)
    syncEngine(signal)

    const feed = setInterval(() => syncPrices(signal), 3000)
    const state = setInterval(() => syncEngine(signal), 5000)
    const clock = setInterval(() => setNowMs(Date.now()), 1000)
    setNowMs(Date.now())

    const onVisible = () => {
      if (document.visibilityState === "visible") {
        syncPrices(signal)
        syncEngine(signal)
      }
    }
    document.addEventListener("visibilitychange", onVisible)

    return () => {
      ac.abort()
      clearInterval(feed)
      clearInterval(state)
      clearInterval(clock)
      document.removeEventListener("visibilitychange", onVisible)
    }
  }, [syncPrices, syncEngine])

  const pnl = engine ? engine.bankroll - engine.bankrollBase : 0
  const pnlPct = engine && engine.bankrollBase > 0 ? (pnl / engine.bankrollBase) * 100 : 0
  const roundLeft = engine && nowMs !== null ? engine.roundEndsAt - nowMs : null
  const regimeMode = engine?.regime?.mode ?? "—"
  const regimeOk = regimeMode === "normal"

  const openRounds = (engine?.rounds || [])
    .filter(r => r.status === "open")
    .sort((a, b) => a.expiresAt - b.expiresAt)

  const recentRounds = (engine?.rounds || [])
    .filter(r => r.status !== "open")
    .sort((a, b) => (b.settledAt ?? b.expiresAt) - (a.settledAt ?? a.expiresAt))
    .slice(0, 14)

  return (
    <div className="fable">
      <div className="f-shell">
        {/* ---------------- Masthead ---------------- */}
        <div className="f-masthead">
          <Link href="/" className="f-brand">
            <span className="f-brand-mark">P</span>
            <span>
              <div className="f-brand-name">Prospera</div>
              <div className="f-brand-sub">LIVE DESK · INVITE ONLY</div>
            </span>
          </Link>

          <div className="f-masthead-meta">
            <span className={`f-led ${feedLive ? "ok" : "warm"}`}>
              {feedLive ? "HYPERLIQUID FEED · LIVE" : "FEED SYNCING…"}
            </span>
            <span className={`f-led ${regimeOk ? "ok" : "warm"}`}>
              REGIME · {regimeMode.toUpperCase()}
            </span>
            <span className="f-clock f-mono">
              {nowMs === null ? "--:--:--" : new Date(nowMs).toISOString().slice(11, 19) + " UTC"}
            </span>
            <ThemeToggle compact />
            {isOwner && (
              <Link href="/dashboard" className="f-btn" style={{ textDecoration: "none" }}>
                FULL DESK →
              </Link>
            )}
            <form action={signOutFromLive}>
              <button type="submit" className="f-btn">SIGN OUT</button>
            </form>
          </div>
        </div>

        <div className="f-wire">
          <div className="f-wire-inner">
            {/* Duplicated once: the marquee keyframe translates by -50%, so the
                second copy is what keeps the ribbon seamless. Fragments, not
                wrapper elements — .f-wire-inner span::before paints a bullet on
                every span, so a wrapper would render a stray one. */}
            {[0, 1].map(i => (
              <Fragment key={i}>
                <span>WATCH-ONLY ACCESS · {user.email}</span>
                <span>5-MINUTE BINARY ROUNDS</span>
                <span>SERVER-VERIFIED SETTLEMENT</span>
                <span>HASH-CHAINED LEDGER</span>
                <span>TRADE-ONLY PERMISSIONS</span>
              </Fragment>
            ))}
          </div>
        </div>

        {engineError && (
          <div className="f-banner err">
            <span className="f-mono" style={{ fontSize: 11 }}>{engineError}</span>
          </div>
        )}

        {!regimeOk && engine?.regime?.reason && (
          <div className="f-banner" style={{ borderColor: "rgba(255, 209, 102, 0.4)", background: "rgba(255, 209, 102, 0.07)", color: "var(--gold)" }}>
            <span className="f-mono" style={{ fontSize: 11 }}>
              REGIME GUARD · {regimeMode.toUpperCase()} — {engine.regime.reason}
            </span>
          </div>
        )}

        {/* ---------------- Ticker tape ---------------- */}
        <div className="f-tape">
          {ASSETS.map(a => {
            const ctx = contexts[a.key]
            const dir = tickDir[a.key]
            const enabled = engine?.assetEnabled?.[a.key]
            // cursor reset: .f-tape-cell is a selectable control on the desk,
            // but nothing is selectable on a watch-only page.
            return (
              <div className="f-tape-cell" key={a.key} style={{ cursor: "default" }}>
                <div className="f-tape-head">
                  <span className="f-kicker">{a.label}</span>
                  <span className={`f-tag ${enabled === false ? "dim" : "azure"}`}>
                    {enabled === false ? "PAUSED" : a.sub}
                  </span>
                </div>
                <div className={`f-tape-price ${dir === "up" ? "tick-up" : dir === "down" ? "tick-down" : ""}`}>
                  {fmtUsd(prices[a.key])}
                </div>
                <div className="f-tape-row">
                  <span className={ctx ? (ctx.change24hPct >= 0 ? "f-pos" : "f-neg") : "f-faint"}>
                    {ctx ? `${ctx.change24hPct >= 0 ? "▲" : "▼"} ${Math.abs(ctx.change24hPct).toFixed(2)}%` : "24H —"}
                  </span>
                  <span>FUND <b>{ctx ? (ctx.fundingRate * 100).toFixed(4) + "%" : "—"}</b></span>
                  <span>OI <b>{fmtCompact(ctx?.openInterest)}</b></span>
                  <span>VOL <b>{fmtCompact(ctx?.dayVolumeUsd)}</b></span>
                </div>
              </div>
            )
          })}
        </div>

        {/* ---------------- Engine stats ---------------- */}
        <div className="f-stat-grid">
          <div className="f-stat">
            <span className="f-kicker">DEMO BANKROLL</span>
            <div className="f-stat-value">{engine ? fmtUsd(engine.bankroll) : "— — —"}</div>
            <div className="f-stat-sub">
              BASE {engine ? fmtUsd(engine.bankrollBase, 0) : "—"}
            </div>
          </div>

          <div className="f-stat">
            <span className="f-kicker">NET P&amp;L</span>
            <div className={`f-stat-value ${engine ? (pnl >= 0 ? "f-pos" : "f-neg") : ""}`}>
              {engine ? fmtSignedUsd(pnl) : "— — —"}
            </div>
            <div className="f-stat-sub">
              {engine ? `${pnl >= 0 ? "+" : "−"}${Math.abs(pnlPct).toFixed(2)}% ON BASE` : "—"}
            </div>
          </div>

          <div className="f-stat">
            <span className="f-kicker">NEXT SETTLEMENT</span>
            <div className="f-stat-value f-azure">
              {roundLeft === null ? "--:--" : fmtClock(roundLeft)}
            </div>
            <div className="f-stat-sub">5-MIN ROUND CLOCK</div>
          </div>

          <div className="f-stat">
            <span className="f-kicker">OPEN ROUNDS</span>
            <div className="f-stat-value">{engine ? openRounds.length : "—"}</div>
            <div className="f-stat-sub">
              QUOTA ROLL {engine ? fmtTime(engine.quotaResetAt) : "—"}
            </div>
          </div>
        </div>

        <div className="f-grid-main">
          <div className="f-col">
            {/* ---------------- Open rounds ---------------- */}
            <div className="f-panel">
              <div className="f-panel-head">
                <h2 className="f-panel-title">
                  <span className="f-serif-grad">Open</span> rounds
                </h2>
                <span className="f-kicker">LIVE · SETTLES ON CANDLE CLOSE</span>
              </div>
              {openRounds.length === 0 ? (
                <div className="f-empty">
                  {engine ? "NO OPEN ROUNDS — ENGINE IS FLAT" : "LOADING ENGINE STATE…"}
                </div>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table className="f-table">
                    <thead>
                      <tr>
                        <th>ASSET</th>
                        <th>SIDE</th>
                        <th className="num">STRIKE</th>
                        <th className="num">ENTRY</th>
                        <th className="num">MARK</th>
                        <th className="num">SIZE</th>
                        <th className="num">EXPIRES</th>
                      </tr>
                    </thead>
                    <tbody>
                      {openRounds.map(r => {
                        const mark = prices[r.asset] ?? engine?.marks?.[r.asset]
                        const ref = r.entryPrice ?? r.strikePrice
                        const inMoney = r.side
                          ? (r.side === "BUY" ? (mark ?? 0) > ref : (mark ?? 0) < ref)
                          : null
                        return (
                          <tr key={r.id}>
                            <td style={{ color: "var(--ivory)" }}>{r.asset}</td>
                            <td>
                              {r.side ? (
                                <span className={`f-tag ${r.side === "BUY" ? "win" : "loss"}`}>{r.side}</span>
                              ) : (
                                <span className="f-tag dim">FLAT</span>
                              )}
                            </td>
                            <td className="num">{fmtUsd(r.strikePrice)}</td>
                            <td className="num">{r.entryPrice ? fmtUsd(r.entryPrice) : "—"}</td>
                            <td className={`num ${inMoney === null ? "" : inMoney ? "f-pos" : "f-neg"}`}>
                              {fmtUsd(mark)}
                            </td>
                            <td className="num">{r.size ?? "—"}</td>
                            <td className="num f-azure">
                              {nowMs === null ? "--:--" : fmtClock(r.expiresAt - nowMs)}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* ---------------- Recent settlements ---------------- */}
            <div className="f-panel">
              <div className="f-panel-head">
                <h2 className="f-panel-title">
                  <span className="f-serif-grad">Settled</span> history
                </h2>
                <span className="f-kicker">SERVER-RECOMPUTED AT EXPIRY</span>
              </div>
              {recentRounds.length === 0 ? (
                <div className="f-empty">
                  {engine ? "NO SETTLED ROUNDS YET" : "LOADING…"}
                </div>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table className="f-table">
                    <thead>
                      <tr>
                        <th>ASSET</th>
                        <th>STATUS</th>
                        <th>SIDE</th>
                        <th className="num">STRIKE</th>
                        <th className="num">ENTRY</th>
                        <th className="num">SETTLED</th>
                        <th>NOTE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recentRounds.map(r => (
                        <tr key={r.id}>
                          <td style={{ color: "var(--ivory)" }}>{r.asset}</td>
                          <td>
                            <span className={`f-tag ${r.status === "settled" ? "azure" : "dim"}`}>
                              {r.status.toUpperCase()}
                            </span>
                          </td>
                          <td>{r.side ?? "—"}</td>
                          <td className="num">{fmtUsd(r.strikePrice)}</td>
                          <td className="num">{r.entryPrice ? fmtUsd(r.entryPrice) : "—"}</td>
                          <td className="num">{fmtTime(r.settledAt ?? r.expiresAt)}</td>
                          <td style={{ maxWidth: 190, overflow: "hidden", textOverflow: "ellipsis" }}>
                            {r.skipReason || "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* ---------------- Level lanes ---------------- */}
          <div className="f-col">
            <div className="f-panel">
              <div className="f-panel-head">
                <h2 className="f-panel-title">
                  <span className="f-serif-grad">Capital</span> lanes
                </h2>
                <span className="f-kicker">PER-TIER ENVELOPE</span>
              </div>

              {!engine ? (
                <div className="f-empty">LOADING LANES…</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {engine.levels.map(l => (
                    <div key={l.level} style={{ borderBottom: "1px solid var(--hairline)", paddingBottom: 11 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 10 }}>
                        <span className="f-mono" style={{ fontSize: 11.5, color: "var(--ivory)" }}>
                          {l.label}
                        </span>
                        <span className={`f-mono f-num ${l.pnl >= 0 ? "f-pos" : "f-neg"}`} style={{ fontSize: 13, fontWeight: 700 }}>
                          {fmtSignedUsd(l.pnl)}
                        </span>
                      </div>
                      <div className="f-tape-row" style={{ marginTop: 6 }}>
                        <span>W/L <b>{l.wins}/{l.losses}</b></span>
                        <span>
                          TODAY{" "}
                          <b className={l.pnlToday >= 0 ? "f-pos" : "f-neg"}>
                            {fmtSignedUsd(l.pnlToday)}
                          </b>
                        </span>
                        <span>
                          TRADES <b>{l.tradesToday}{l.dailyTrades ? `/${l.dailyTrades}` : ""}</b>
                        </span>
                        <span>BANK <b>{l.bankroll === null ? "∞" : fmtUsd(l.bankroll, 0)}</b></span>
                      </div>
                      <div style={{ marginTop: 7, display: "flex", gap: 6, flexWrap: "wrap" }}>
                        {l.uncapped && <span className="f-tag gold">UNCAPPED</span>}
                        {l.dailyStopActive && <span className="f-tag loss">LOSS BREAKER</span>}
                        {l.profitLockActive && <span className="f-tag win">PROFIT LOCK</span>}
                        {!l.uncapped && !l.dailyStopActive && !l.profitLockActive && (
                          <span className="f-tag dim">TRADING</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="f-panel">
              <div className="f-panel-head">
                <h2 className="f-panel-title">
                  <span className="f-serif-grad">Access</span> notice
                </h2>
              </div>
              <p style={{ margin: 0, fontSize: 11.5, lineHeight: 1.75, color: "var(--ivory-dim)" }}>
                You are signed in as <b className="f-azure">{user.email}</b> with watch-only access.
                This page mirrors the canonical engine — it exposes no controls, and every mutating
                endpoint remains owner-gated.
              </p>
              <hr className="f-divider" />
              <p style={{ margin: 0, fontSize: 10.5, lineHeight: 1.7, color: "var(--ivory-faint)" }}>
                Demo results are paper-traded on live marks. Trading involves risk and can result in
                loss. Past and simulated performance do not indicate future results.
              </p>
            </div>
          </div>
        </div>

        <div className="f-section-head" style={{ marginTop: 30 }}>
          <span className="f-kicker">PROSPERA · LIVE DESK</span>
        </div>
        <p className="f-kicker" style={{ lineHeight: 1.8 }}>
          FEED: HYPERLIQUID L1 · SETTLEMENT: SERVER-VERIFIED · ACCESS: INVITATION ONLY
        </p>
      </div>
    </div>
  )
}
