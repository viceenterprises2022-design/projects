import { getSessionInfo } from "@/lib/authz"
import { redirect } from "next/navigation"
import LedgerClient from "./LedgerClient"
import "../../dashboard/dashboard.css"

export const dynamic = "force-dynamic"

export default async function AdminLedgerPage() {
  const { user, isOwner } = await getSessionInfo()
  if (!user) redirect("/login")
  if (!isOwner) redirect("/dashboard")
  return <LedgerClient />
}
