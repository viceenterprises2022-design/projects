import DashboardClient from "./DashboardClient"
import { getSessionInfo } from "@/lib/authz"

export const dynamic = "force-dynamic"

export default async function DashboardPage() {
  const { user, isOwner } = await getSessionInfo()
  return <DashboardClient user={user} isOwner={isOwner} />
}
