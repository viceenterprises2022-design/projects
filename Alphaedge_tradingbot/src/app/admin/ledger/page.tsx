import { getSessionInfo } from "@/lib/authz"
import { redirect } from "next/navigation"
import LedgerClient from "./LedgerClient"
import "../../demo/demo.css"

export const dynamic = "force-dynamic"

export default async function AdminLedgerPage() {
  const { user, isOwner } = await getSessionInfo()
  if (!user) redirect("/login")
  if (!isOwner) redirect("/demo")
  return <LedgerClient />
}
