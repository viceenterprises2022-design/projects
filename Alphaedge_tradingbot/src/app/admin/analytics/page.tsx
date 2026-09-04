import { getSessionInfo } from "@/lib/authz"
import { redirect } from "next/navigation"
import AnalyticsClient from "./AnalyticsClient"
import "../../demo/demo.css"

export const dynamic = "force-dynamic"

export default async function AdminAnalyticsPage() {
  const { user, isOwner } = await getSessionInfo()
  if (!user) redirect("/login")
  if (!isOwner) redirect("/demo")
  return <AnalyticsClient isOwner />
}
