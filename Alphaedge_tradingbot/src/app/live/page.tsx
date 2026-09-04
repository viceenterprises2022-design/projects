import type { Metadata } from "next"
import type { ReactNode } from "react"
import Link from "next/link"
import LiveClient from "./LiveClient"
import ThemeToggle from "../ThemeToggle"
import { getSessionInfo } from "@/lib/authz"
import { signInToLive, signOutFromLive } from "./live-actions"
import "../dashboard/dashboard.css"

export const dynamic = "force-dynamic"

// Invite-only: keep it out of search results and crawler caches. The page is
// unlisted by design — nothing on the public site links to it.
export const metadata: Metadata = {
  title: "Live Desk — Prospera",
  robots: { index: false, follow: false, nocache: true, googleBot: { index: false, follow: false } },
}

// Shared chrome for every locked state, so the sign-in, pending and declined
// screens are visually identical to /login and the dashboard's gate.
function Gate({ children }: { children: ReactNode }) {
  return (
    <div className="fable">
      <div style={{ position: "fixed", top: 18, right: 18, zIndex: 10 }}>
        <ThemeToggle />
      </div>
      <div className="f-loading-shell" style={{ gap: 26 }}>
        <Link href="/" className="f-brand" style={{ flexDirection: "column", gap: 14, textAlign: "center" }}>
          <span className="f-brand-mark" style={{ width: 52, height: 52, fontSize: 22, borderRadius: 18 }}>P</span>
          <span>
            <div className="f-brand-name" style={{ fontSize: 26 }}>Prospera</div>
            <div className="f-brand-sub">LIVE DESK · INVITE ONLY</div>
          </span>
        </Link>

        <div className="f-panel" style={{ width: "min(430px, 92vw)", padding: "28px 26px", textAlign: "center" }}>
          {children}
        </div>

        <span className="f-kicker">Feed: Hyperliquid L1 · Settlement: server-verified · Watch-only</span>
      </div>
    </div>
  )
}

export default async function LivePage() {
  const { user, isOwner, canView, role } = await getSessionInfo()

  // Anonymous — show only branding and a sign-in button. No market or engine
  // data is fetched or rendered on this branch.
  if (!user) {
    return (
      <Gate>
        <div className="f-serif-grad" style={{ fontSize: 32, fontStyle: "normal", marginBottom: 10 }}>
          Live Desk
        </div>
        <p style={{ margin: "0 0 22px", fontSize: 12.5, lineHeight: 1.7, color: "var(--ivory-dim)" }}>
          This page streams the live engine and is limited to invited accounts.
          Sign in to check your access.
        </p>
        <form action={signInToLive}>
          <button type="submit" className="f-btn primary" style={{ width: "100%", padding: "12px 16px", fontSize: 12 }}>
            CONTINUE WITH GOOGLE
          </button>
        </form>
        <div style={{ marginTop: 18 }}>
          <Link href="/" className="f-kicker" style={{ textDecoration: "none" }}>← prospera home</Link>
        </div>
      </Gate>
    )
  }

  // Signed in, but not on the access list.
  if (!canView) {
    return (
      <Gate>
        {role === "blocked" ? (
          <>
            <div className="f-serif-grad" style={{ fontSize: 24, marginBottom: 10 }}>access declined</div>
            <p style={{ margin: "0 0 18px", fontSize: 12.5, lineHeight: 1.7, color: "var(--ivory-dim)" }}>
              The account <b style={{ color: "var(--azure)" }}>{user.email}</b> has been declined by
              the desk operator.
            </p>
          </>
        ) : (
          <>
            <div className="f-serif-grad" style={{ fontSize: 24, marginBottom: 10 }}>awaiting approval</div>
            <p style={{ margin: "0 0 18px", fontSize: 12.5, lineHeight: 1.7, color: "var(--ivory-dim)" }}>
              <b style={{ color: "var(--azure)" }}>{user.email}</b> is signed in but not yet on the
              live-desk access list. The desk operator approves viewers from the Access Control panel.
            </p>
            <div className="f-chip" style={{ marginBottom: 18 }}>
              <span className="f-kicker">STATUS</span>
              <b className="f-gold">PENDING</b>
            </div>
          </>
        )}
        <form action={signOutFromLive}>
          <button type="submit" className="f-btn" style={{ padding: "8px 18px", fontSize: 10.5 }}>
            SIGN OUT
          </button>
        </form>
        <div style={{ marginTop: 16 }}>
          <Link href="/" className="f-kicker" style={{ textDecoration: "none" }}>← prospera home</Link>
        </div>
      </Gate>
    )
  }

  return <LiveClient user={{ name: user.name, email: user.email }} isOwner={isOwner} />
}
