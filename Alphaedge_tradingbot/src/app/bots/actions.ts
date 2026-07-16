"use server"

import { db } from "@/db"
import { exchangeConnections, botInstances } from "@/db/schema"
import { revalidatePath } from "next/cache"
import { eq } from "drizzle-orm"

const SYSTEM_USER_ID = "system-user"

export async function subscribeToBot(formData: FormData) {
  const userId = SYSTEM_USER_ID
  const botTemplateId = formData.get("botTemplateId") as string
  
  if (!botTemplateId) throw new Error("Missing bot template ID")

  // Check if user has an exchange connection
  const connections = await db.select().from(exchangeConnections).where(eq(exchangeConnections.userId, userId))
  
  let connectionId = ""
  
  if (connections.length === 0) {
    // Create a default paper trading connection for onboarding purposes
    connectionId = `conn_${crypto.randomUUID()}`
    await db.insert(exchangeConnections).values({
      id: connectionId,
      userId,
      exchange: 'paper',
      encryptedApiKey: 'mock_key',
      encryptionIv: 'mock_iv',
      encryptionTag: 'mock_tag',
      lastVerifiedAt: Date.now()
    })
  } else {
    connectionId = connections[0].id
  }

  // Subscribe user to the bot instance
  await db.insert(botInstances).values({
    id: `inst_${crypto.randomUUID()}`,
    userId,
    botTemplateId,
    exchangeConnectionId: connectionId,
    mode: 'paper',
    riskCeilingPct: 5.0,
    maxNotional: 10000.0,
    status: 'active'
  })

  revalidatePath("/bots")
}
