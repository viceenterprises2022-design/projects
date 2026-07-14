"use client";

import { FormEvent, useMemo, useState } from "react";

type FormState = "idle" | "loading" | "success" | "error";

const roles = ["Solo allocator", "Founder / operator", "Family office", "Advisor", "Quant builder"];
const capitalBands = ["Exploring", "$1k-$10k", "$10k-$100k", "$100k+", "Institutional"];
const marketFocuses = ["Multi-asset", "Crypto", "Commodities", "FX", "Equities"];

export function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState(roles[0]);
  const [capitalBand, setCapitalBand] = useState(capitalBands[0]);
  const [marketFocus, setMarketFocus] = useState(marketFocuses[0]);
  const [state, setState] = useState<FormState>("idle");
  const [message, setMessage] = useState("Reserve your private launch seat.");

  const buttonCopy = useMemo(() => {
    if (state === "loading") return "Securing access...";
    if (state === "success") return "Access requested";
    return "Join private launch";
  }, [state]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");
    setMessage("Routing your invite request through the capital mesh...");

    try {
      const response = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, role, capitalBand, marketFocus }),
      });
      const data = (await response.json()) as { ok?: boolean; message?: string };

      if (!response.ok || !data.ok) {
        throw new Error(data.message ?? "Something went wrong.");
      }

      setState("success");
      setMessage(data.message ?? "You are on the private launch list.");
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "Try again shortly.");
    }
  }

  return (
    <form onSubmit={onSubmit} className="launch-form" id="launch">
      <div className="form-grid">
        <label className="field-shell field-shell-wide">
          <span>Email for your invite</span>
          <input
            required
            type="email"
            value={email}
            placeholder="you@domain.com"
            onChange={(event) => setEmail(event.target.value)}
            disabled={state === "loading" || state === "success"}
          />
        </label>
        <label className="field-shell">
          <span>Profile</span>
          <select value={role} onChange={(event) => setRole(event.target.value)} disabled={state === "loading"}>
            {roles.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field-shell">
          <span>Capital range</span>
          <select
            value={capitalBand}
            onChange={(event) => setCapitalBand(event.target.value)}
            disabled={state === "loading"}
          >
            {capitalBands.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field-shell field-shell-wide">
          <span>First market universe</span>
          <select
            value={marketFocus}
            onChange={(event) => setMarketFocus(event.target.value)}
            disabled={state === "loading"}
          >
            {marketFocuses.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>

      <button type="submit" className="launch-button" disabled={state === "loading" || state === "success"}>
        <span>{buttonCopy}</span>
        <span aria-hidden="true">↗</span>
      </button>
      <p className={`form-message ${state}`}>{message}</p>
    </form>
  );
}
