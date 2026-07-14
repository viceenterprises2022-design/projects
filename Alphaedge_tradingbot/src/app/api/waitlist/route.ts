import { db } from "@/db";
import { earlyAccessLeads } from "@/db/schema";
import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

type WaitlistPayload = {
  email?: unknown;
  role?: unknown;
  capitalBand?: unknown;
  marketFocus?: unknown;
};

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function safeText(value: unknown, fallback: string, maxLength: number) {
  if (typeof value !== "string") {
    return fallback;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return fallback;
  }

  return trimmed.slice(0, maxLength);
}

export async function POST(request: NextRequest) {
  let payload: WaitlistPayload;

  try {
    payload = (await request.json()) as WaitlistPayload;
  } catch {
    return Response.json({ ok: false, message: "Send a valid JSON payload." }, { status: 400 });
  }

  const email = safeText(payload.email, "", 256).toLowerCase();

  if (!emailPattern.test(email)) {
    return Response.json({ ok: false, message: "Enter a valid email address." }, { status: 400 });
  }

  const role = safeText(payload.role, "capital-builder", 80);
  const capitalBand = safeText(payload.capitalBand, "exploring", 80);
  const marketFocus = safeText(payload.marketFocus, "multi-asset", 120);

  try {
    const [lead] = await db
      .insert(earlyAccessLeads)
      .values({
        email,
        role,
        capitalBand,
        marketFocus,
        createdAt: Date.now()
      })
      .onConflictDoUpdate({
        target: earlyAccessLeads.email,
        set: { role, capitalBand, marketFocus },
      })
      .returning({ id: earlyAccessLeads.id, createdAt: earlyAccessLeads.createdAt });

    return Response.json({
      ok: true,
      message: "You are on the private launch list.",
      lead,
    });
  } catch (error) {
    console.error("waitlist_insert_failed", error);
    return Response.json(
      { ok: false, message: "We could not save your invite request. Try again shortly." },
      { status: 500 },
    );
  }
}
