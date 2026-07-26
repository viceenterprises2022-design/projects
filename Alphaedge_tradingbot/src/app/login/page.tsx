import { redirect } from "next/navigation"
import Link from "next/link"
import ThemeToggle from "../ThemeToggle"
import { getSessionInfo } from "@/lib/authz"
import { handleGoogleSignIn } from "@/app/auth-actions"
import "../dashboard/dashboard.css"

export const dynamic = "force-dynamic"

export default async function LoginPage() {
  const { user } = await getSessionInfo()
  if (user) redirect("/dashboard")

  return (
    <div className="fable">
      {/* Fixed, not in a header: the sign-in screen has no nav bar, and this is
          where a light-mode reader most often lands with no other way back. */}
      <div style={{ position: "fixed", top: 18, right: 18, zIndex: 10 }}>
        <ThemeToggle />
      </div>
      <div className="f-loading-shell" style={{ gap: 26 }}>
        <Link href="/" className="f-brand" style={{ flexDirection: "column", gap: 14, textAlign: "center" }}>
          <span className="f-brand-mark" style={{ width: 52, height: 52, fontSize: 22, borderRadius: 18 }}>P</span>
          <span>
            <div className="f-brand-name" style={{ fontSize: 26 }}>Prospera</div>
            <div className="f-brand-sub">CAPITAL COCKPIT</div>
          </span>
        </Link>

        <div className="f-panel" style={{ width: "min(400px, 92vw)", padding: "28px 26px", textAlign: "center" }}>
          <div className="f-serif-grad" style={{ fontSize: 34, fontStyle: "normal", marginBottom: 10 }}>Operator Sign-In</div>
          <p style={{ margin: "0 0 22px", fontSize: 12.5, lineHeight: 1.7, color: "var(--ivory-dim)" }}>
            Sign in with Google to access the demo desk. Viewing is limited to
            invited accounts; the operator manages the access list.
          </p>
          <form action={handleGoogleSignIn}>
            <button type="submit" className="f-btn primary" style={{ width: "100%", padding: "12px 16px", fontSize: 12 }}>
              CONTINUE WITH GOOGLE
            </button>
          </form>
          <div style={{ marginTop: 18 }}>
            <Link href="/" className="f-kicker" style={{ textDecoration: "none" }}>
              ← prospera home
            </Link>
          </div>
        </div>

        <span className="f-kicker">Feed: Hyperliquid L1 · Ledger: Turso · Settlement: server-verified</span>
      </div>
    </div>
  )
}
