import { getSessionInfo } from "@/lib/authz"
import { redirect } from "next/navigation"
import Link from "next/link"
import { CHANGELOG, TAG_STYLE } from "./changelog-data"
import "../dashboard/dashboard.css"

export const dynamic = "force-dynamic"

// Product changelog for signed-in viewers. Entries live in a version-
// controlled file and ship with the change they describe, so the log cannot
// drift from the product — and the page costs zero database reads.
export default async function ChangelogPage() {
  const { user, canView } = await getSessionInfo()
  if (!user) redirect("/login")
  if (!canView) redirect("/dashboard")

  // Group by date, preserving the order entries are declared in
  const days: Array<{ date: string; entries: typeof CHANGELOG }> = []
  for (const entry of CHANGELOG) {
    const last = days[days.length - 1]
    if (last && last.date === entry.date) last.entries.push(entry)
    else days.push({ date: entry.date, entries: [entry] })
  }

  const fmtDate = (iso: string) =>
    new Date(iso + "T00:00:00Z").toLocaleDateString("en-GB", {
      day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
    })

  return (
    <div className="fable">
      <div className="f-shell">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12, margin: "18px 0 8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <span className="f-brand-mark" style={{ width: 40, height: 40, fontSize: 17, borderRadius: 13 }}>P</span>
            <div>
              <div className="f-serif-grad" style={{ fontSize: 22 }}>What&rsquo;s Changed</div>
              <div className="f-kicker">PRODUCT CHANGELOG · NEWEST FIRST</div>
            </div>
          </div>
          <Link href="/dashboard" className="f-btn" style={{ padding: "7px 14px", fontSize: 10, textDecoration: "none" }}>← COCKPIT</Link>
        </div>

        <p style={{ margin: "0 0 20px", fontSize: 13, lineHeight: 1.75, color: "var(--ivory-dim)", maxWidth: 760 }}>
          Every change to how the desk trades, and every change to what you can see, is recorded here — including
          the ones we tested and decided against. The demo period is when the system is tuned, so results from
          different days may have been produced under different settings.
        </p>

        {days.map(day => (
          <div key={day.date} style={{ marginBottom: 26 }}>
            <div className="f-kicker" style={{ marginBottom: 10, color: "var(--azure)" }}>{fmtDate(day.date)}</div>
            <div style={{ display: "grid", gap: 10 }}>
              {day.entries.map(entry => (
                <div className="f-panel" key={entry.title} style={{ padding: "15px 18px" }}>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap", marginBottom: 6 }}>
                    <span className={`f-tag ${TAG_STYLE[entry.tag]}`}>{entry.tag.toUpperCase()}</span>
                    <span style={{ fontSize: 14.5, fontWeight: 600, color: "var(--ivory)" }}>{entry.title}</span>
                  </div>
                  <p style={{ margin: 0, fontSize: 13, lineHeight: 1.75, color: "var(--ivory-dim)" }}>{entry.body}</p>
                </div>
              ))}
            </div>
          </div>
        ))}

        <p className="f-mono f-faint" style={{ fontSize: 9, margin: "4px 2px 28px", letterSpacing: "0.05em", lineHeight: 1.7 }}>
          Thresholds described here are limits at which trading pauses, not projected or promised returns. Demo
          results are produced with practice capital against live market prices and do not indicate future performance.
        </p>
      </div>
    </div>
  )
}
