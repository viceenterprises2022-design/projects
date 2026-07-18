import { ImageResponse } from "next/og"

export const size = { width: 1200, height: 630 }
export const contentType = "image/png"
export const alt = "Prospera — turn idle capital into an autonomous wealth system"

// Social share card: brand chip + headline on the desk's navy field
export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 72,
          background: "#050711",
          backgroundImage:
            "radial-gradient(700px 400px at 85% 0%, rgba(88,240,255,0.16), transparent 60%), radial-gradient(600px 420px at 0% 100%, rgba(157,125,255,0.15), transparent 55%)",
          color: "#f4f7ff",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div
            style={{
              width: 72,
              height: 72,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: 22,
              background: "linear-gradient(135deg, #58f0ff 0%, #bfff6a 55%, #9d7dff 100%)",
              color: "#051016",
              fontSize: 40,
              fontWeight: 800,
            }}
          >
            P
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: 36, fontWeight: 700 }}>Prospera</div>
            <div style={{ fontSize: 16, letterSpacing: 4, color: "rgba(239,246,255,0.5)" }}>
              WEALTH AUTOMATION CLOUD
            </div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 26 }}>
          <div style={{ fontSize: 66, fontWeight: 750, lineHeight: 1.04, letterSpacing: -2, maxWidth: 950 }}>
            Turn idle capital into an autonomous wealth system.
          </div>
          <div style={{ display: "flex", gap: 14 }}>
            {["LIVE DEMO DESK", "90S VERIFIABLE ROUNDS", "0 WITHDRAWAL PERMISSIONS"].map(chip => (
              <div
                key={chip}
                style={{
                  display: "flex",
                  fontSize: 17,
                  fontWeight: 700,
                  letterSpacing: 2,
                  color: "#bfff6a",
                  border: "1px solid rgba(191,255,106,0.4)",
                  borderRadius: 999,
                  padding: "12px 22px",
                  background: "rgba(191,255,106,0.08)",
                }}
              >
                {chip}
              </div>
            ))}
          </div>
        </div>
      </div>
    ),
    { ...size }
  )
}
