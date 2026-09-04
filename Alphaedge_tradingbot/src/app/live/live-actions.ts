"use server"

import { signIn, signOut } from "@/auth"

// Dedicated to /live so the OAuth round trip returns here rather than to the
// desk — a viewer invited to the live page should land back on the live page.
export async function signInToLive() {
  await signIn("google", { redirectTo: "/live" })
}

export async function signOutFromLive() {
  await signOut({ redirectTo: "/" })
}
