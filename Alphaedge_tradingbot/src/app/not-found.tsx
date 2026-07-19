import Link from "next/link"
import "./landing.css"

export default function NotFound() {
  return (
    <main className="landing">
      <div className="l-noise" aria-hidden="true" />
      <div
        className="l-shell"
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 26,
          textAlign: "center",
        }}
      >
        <span className="l-brand-mark" style={{ width: 56, height: 56, fontSize: 24, borderRadius: 18 }}>P</span>
        <div>
          <div className="l-kicker">Error 404 · Route not on the ledger</div>
          <h1 style={{ margin: "18px 0 0", fontSize: "clamp(40px, 6vw, 72px)", lineHeight: 1, letterSpacing: "-0.03em" }}>
            This page went <span className="l-serif-grad">off-market.</span>
          </h1>
          <p style={{ margin: "20px auto 0", maxWidth: 440, fontSize: 15, lineHeight: 1.7, color: "var(--dim)" }}>
            The address you followed doesn't settle anywhere. The desk, however, is still live.
          </p>
        </div>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center" }}>
          <Link href="/" className="l-btn-primary">Back to Prospera</Link>
          <Link href="/dashboard" className="l-btn-ghost">Watch the live desk</Link>
        </div>
      </div>
    </main>
  )
}
