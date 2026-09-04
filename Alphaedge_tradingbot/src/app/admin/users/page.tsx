import { getSessionInfo } from "@/lib/authz"
import { redirect } from "next/navigation"
import UsersClient from "./UsersClient"
import "../../demo/demo.css"

export const dynamic = "force-dynamic"

export default async function AdminUsersPage() {
  const { user, isOwner } = await getSessionInfo()
  if (!user) redirect("/login")
  if (!isOwner) redirect("/demo")
  return <UsersClient selfEmail={user.email ?? ''} />
}
