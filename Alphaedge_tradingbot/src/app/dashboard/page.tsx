import DashboardClient from "./DashboardClient"
import OnboardingGate from "./OnboardingGate"
import { getSessionInfo } from "@/lib/authz"
import { redirect } from "next/navigation"
import Link from "next/link"
import { handleSignOut } from "@/app/auth-actions"
import { db } from "@/db"
import { initDb } from "@/db/init"
import { onboardingProfiles } from "@/db/schema"
import { eq } from "drizzle-orm"
import "./dashboard.css"

export const dynamic = "force-dynamic"

export default async function DashboardPage() {
  const { user, isOwner, canView, role } = await getSessionInfo()

  if (!user) redirect("/login")

  if (!canView) {
    const email = user.email?.toLowerCase() || ""
    let existing = null
    if (role !== "blocked" && email) {
      try {
        await initDb()
        const rows = await db.select().from(onboardingProfiles)
          .where(eq(onboardingProfiles.email, email)).limit(1)
        if (rows[0]) {
          existing = {
            fullName: rows[0].fullName,
            levelInterest: rows[0].levelInterest,
            capitalBand: rows[0].capitalBand,
            experience: rows[0].experience,
            note: rows[0].note,
          }
        }
      } catch { /* table may not exist yet on first boot — form still works */ }
    }
    return (
      <div className="fable">
        <div className="f-loading-shell" style={{ gap: 22 }}>
          <span className="f-brand-mark" style={{ width: 52, height: 52, fontSize: 22, borderRadius: 18 }}>P</span>
          <div className="f-panel" style={{ width: "min(460px, 92vw)", padding: "26px 24px", textAlign: "center" }}>
            {role === "blocked" ? (
              <>
                <div className="f-serif-grad" style={{ fontSize: 21, marginBottom: 10 }}>access declined</div>
                <p style={{ margin: "0 0 18px", fontSize: 12.5, lineHeight: 1.7, color: "var(--ivory-dim)" }}>
                  The account <b style={{ color: "var(--azure)" }}>{user.email}</b> has been declined
                  by the desk operator.
                </p>
              </>
            ) : (
              <OnboardingGate email={email} defaultName={user.name || ""} existing={existing} />
            )}
            <form action={handleSignOut} style={{ marginTop: 14 }}>
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
