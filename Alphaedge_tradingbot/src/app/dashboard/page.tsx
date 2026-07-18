import DashboardClient from "./DashboardClient"
import { getSessionInfo } from "@/lib/authz"
import { redirect } from "next/navigation"
import Link from "next/link"
import { handleSignOut } from "@/app/auth-actions"
import "./dashboard.css"

export const dynamic = "force-dynamic"

export default async function DashboardPage() {
  const { user, isOwner, canView } = await getSessionInfo()

  if (!user) redirect("/login")

  if (!canView) {
    return (
      <div className="fable">
        <div className="f-loading-shell" style={{ gap: 22 }}>
          <span className="f-brand-mark" style={{ width: 52, height: 52, fontSize: 22, borderRadius: 18 }}>P</span>
          <div className="f-panel" style={{ width: "min(420px, 92vw)", padding: "26px 24px", textAlign: "center" }}>
            <div className="f-serif-grad" style={{ fontSize: 21, marginBottom: 10 }}>access pending</div>
            <p style={{ margin: "0 0 8px", fontSize: 12.5, lineHeight: 1.7, color: "var(--ivory-dim)" }}>
              You are signed in as <b style={{ color: "var(--azure)" }}>{user.email}</b>, but this
              account is not on the demo access list yet.
            </p>
            <p style={{ margin: "0 0 18px", fontSize: 12.5, lineHeight: 1.7, color: "var(--ivory-faint)" }}>
              Ask the desk operator to add your email, then reload this page.
            </p>
            <form action={handleSignOut}>
              <button type="submit" className="f-btn" style={{ padding: "8px 18px", fontSize: 10.5 }}>
                SIGN OUT
              </button>
            </form>
          </div>
          <Link href="/" className="f-kicker" style={{ textDecoration: "none" }}>← prospera home</Link>
        </div>
      </div>
    )
  }

  return <DashboardClient user={user} isOwner={isOwner} />
}
