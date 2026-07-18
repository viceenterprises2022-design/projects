import { handlers } from "@/auth"
import { initDb } from "@/db/init"
import type { NextRequest } from "next/server"

// Apply pending migrations before any auth operation — sign-in must never
// depend on some other endpoint having migrated the database first.
const { GET: authGET, POST: authPOST } = handlers

export async function GET(req: NextRequest) {
  await initDb()
  return authGET(req)
}

export async function POST(req: NextRequest) {
  await initDb()
  return authPOST(req)
}
