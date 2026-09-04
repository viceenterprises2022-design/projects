import { getSessionInfo } from "@/lib/authz"
import { redirect } from "next/navigation"
import { db } from "@/db"
import { initDb } from "@/db/init"
import { changelogPublications } from "@/db/schema"
import ChangelogClient from "./ChangelogClient"
import "../demo/demo.css"

export const dynamic = "force-dynamic"

// Product changelog. Entry content is version-controlled (an entry ships in the
// same commit as the change it describes, so it cannot drift); only the
// decision to publish is stored, and viewers see published entries only.
export default async function ChangelogPage() {
  const { user, isOwner, canView } = await getSessionInfo()
  if (!user) redirect("/login")
  if (!canView) redirect("/demo")

  let publishedIds: string[] = []
  try {
    await initDb()
    const rows = await db.select({ entryId: changelogPublications.entryId }).from(changelogPublications)
    publishedIds = rows.map(r => r.entryId)
  } catch {
    // Table not migrated yet — treat everything as draft rather than leaking
    // unapproved entries to viewers.
  }

  return <ChangelogClient isOwner={isOwner} publishedIds={publishedIds} />
}
