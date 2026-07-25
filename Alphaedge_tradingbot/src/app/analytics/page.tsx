import { getSessionInfo } from "@/lib/authz"
import { redirect } from "next/navigation"
import AnalyticsClient from "../admin/analytics/AnalyticsClient"
import "../dashboard/dashboard.css"

export const dynamic = "force-dynamic"

// Strategy analytics for every approved viewer. Same component the owner
// route renders; owners additionally get the Ledger Explorer link.
export default async function AnalyticsPage() {
  const { user, isOwner, canView } = await getSessionInfo()
  if (!user) redirect("/login")
  if (!canView) redirect("/dashboard")
  return <AnalyticsClient isOwner={isOwner} />
}
