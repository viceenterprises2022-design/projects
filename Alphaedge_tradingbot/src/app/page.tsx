import Link from "next/link";
import ThemeToggle from "./ThemeToggle";
import { WaitlistForm } from "./waitlist-form";
import { LiveDesk } from "./live-desk";
import "./landing.css";

const wealthLoops = [
  {
    n: "01",
    title: "market regime scanner",
    body: "Reads live volatility, drift, and funding structure before any capital moves — the same telemetry shown on the desk.",
  },
  {
    n: "02",
    title: "risk-budget allocator",
    body: "Every position is sized against a bankroll ceiling and per-asset caps. Nothing trades outside its envelope.",
  },
  {
    n: "03",
    title: "execution engine",
    body: "Deterministic five-minute decision rounds, settled server-side against real candle closes. No hand-waving.",
  },
  {
    n: "04",
    title: "verifiable ledger",
    body: "Outcomes and PnL are recomputed at settlement and persisted. What you see is what actually happened.",
  },
];

const pricing = [
  {
    tier: "Seed",
    level: "Demo",
    price: "0%",
    note: "for exploration",
    perks: ["Watch-only demo desk", "Live engine telemetry", "Verifiable round history"],
  },
  {
    tier: "Builder",
    level: "Level 1",
    price: "1.2%",
    note: "annual platform access",
    perks: ["$5K capital lane", "50 trades per day", "Pauses at +28% daily", "Live bot deployment", "Risk guardrails"],
    featured: true,
  },
  {
    tier: "Compounder",
    level: "Level 2",
    price: "1.8%",
    note: "annual platform access",
    perks: ["$10K capital lane", "100 trades per day", "Pauses at +28% daily", "Everything in Builder", "Priority execution lanes"],
  },
  {
    tier: "Sovereign",
    level: "Level 3",
    price: "Custom",
    note: "for teams and allocators",
    perks: ["$25K+ capital lane", "250 trades per day", "Pauses at +28% daily", "White-glove onboarding", "Custom mandates"],
  },
];

export default function HomePage() {
  return (
    <main className="landing">
      <div className="l-noise" aria-hidden="true" />

      <div className="l-shell">
        {/* ---------- Nav ---------- */}
        <nav className="l-nav l-rise">
          <a href="#top" className="l-brand" aria-label="Prospera home">
            <span className="l-brand-mark">P</span>
            <span>
              <span className="l-brand-name">Prospera</span>
              <span className="l-brand-sub">Wealth Automation Cloud</span>
            </span>
          </a>
          <div className="l-nav-links" aria-label="Primary navigation">
            <a href="#engine">Engine</a>
            <a href="#mandates">Mandates</a>
            <a href="#pricing">Pricing</a>
            <Link href="/login">Access</Link>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <ThemeToggle />
            <Link className="l-nav-cta" href="/login">
              Open the desk
            </Link>
          </div>
        </nav>

        {/* ---------- Hero ---------- */}
        <section id="top" className="l-hero">
          <div>
            <div className="l-pill l-rise l-d1">Live demo desk · trading right now</div>
            <h1 className="l-rise l-d2">
              Turn idle capital into an <span className="l-serif-grad">autonomous wealth&nbsp;system.</span>
            </h1>
            <p className="l-lede l-rise l-d3">
              Prospera turns strategies into governed bots: pick a mandate, set the capital envelope,
              and watch a server-side engine trade deterministic rounds against live markets — with
              trade-only permissions and a ledger you can verify line by line.
            </p>
            <div className="l-hero-actions l-rise l-d4">
              <Link href="/login" className="l-btn-primary">
                Access the platform <span aria-hidden>↗</span>
              </Link>
              <a href="#engine" className="l-btn-ghost">
                How the engine works
              </a>
            </div>
            <div className="l-hero-chips l-rise l-d5" aria-label="Platform guarantees">
              <div className="l-chip">
                <strong>24/7</strong>
                <span>server-side engine</span>
              </div>
              <div className="l-chip">
                <strong>5-min</strong>
                <span>verifiable rounds</span>
              </div>
              <div className="l-chip">
                <strong>0</strong>
                <span>withdrawal permissions</span>
              </div>
            </div>
          </div>

          <LiveDesk />
        </section>
      </div>

      {/* ---------- Live ribbon ---------- */}
      <div className="l-ribbon" aria-hidden="true">
        <div className="l-ribbon-inner">
          {[0, 1].map(dup => (
            <span key={dup} style={{ display: "inline" }}>
              {[
                "XAU · GOLD (PAXG)",
                "BTC · PERPETUAL",
                "ETH · PERPETUAL",
                "HYPERLIQUID L1 FEED",
                "5-MIN BINARY ROUNDS",
                "SERVER-VERIFIED SETTLEMENT",
                "HASH-CHAINED LEDGER",
                "WATCH-ONLY DEMO LIVE",
              ].map(item => (
                <span key={`${dup}-${item}`}>{item}</span>
              ))}
            </span>
          ))}
        </div>
      </div>

      <div className="l-shell">
        {/* ---------- Engine ---------- */}
        <section id="engine" className="l-section">
          <div className="l-section-head">
            <div className="l-kicker">Capital autonomy without surrendering control</div>
            <h2>
              Wealth is a system. Prospera gives it an <span className="l-serif-grad">operating layer.</span>
            </h2>
            <p>
              Instead of another trading terminal, Prospera runs strategies as governed bots. The demo desk
              you can watch today is the same machinery: live feeds in, disciplined execution out, every
              outcome written to a ledger that cannot drift from reality.
            </p>
          </div>

          <div className="l-loops">
            {wealthLoops.map(loop => (
              <article className="l-loop" key={loop.n}>
                <span>{loop.n}</span>
                <h3>{loop.title}</h3>
                <p>{loop.body}</p>
              </article>
            ))}
          </div>
        </section>

        {/* ---------- Mandates ---------- */}
        <section id="mandates" className="l-section">
          <div className="l-split">
            <div>
              <div className="l-kicker">Bot marketplace</div>
              <h2 style={{ margin: "16px 0 0", fontSize: "clamp(32px, 3.8vw, 50px)", lineHeight: 1.06, letterSpacing: "-0.03em" }}>
                Deploy cash through bots that behave like <span className="l-serif-grad">mandates.</span>
              </h2>
              <ul className="l-check">
                <li>Trade-only exchange and broker keys — withdrawal rights are never requested</li>
                <li>Per-bot capital caps, pause rules, and kill switches</li>
                <li>Transparent logs for entries, exits, and risk events</li>
                <li>Multi-market roadmap: crypto and gold today; FX, equities, and custom strategies next</li>
              </ul>
            </div>

            <div className="l-composer" aria-label="Mandate composer preview">
              <div className="l-composer-head">
                <span className="l-kicker">Mandate composer</span>
                <span className="l-led ok">PREVIEW</span>
              </div>
              <div className="l-composer-rows">
                <div className="l-composer-row">
                  <small>Objective</small>
                  <strong>Compound with controlled volatility</strong>
                </div>
                <div className="l-composer-row">
                  <small>Capital lane</small>
                  <strong>$25,000 · user custody</strong>
                </div>
                <div className="l-composer-row">
                  <small>Universe</small>
                  <strong>XAU / BTC / ETH</strong>
                </div>
                <div className="l-composer-row">
                  <small>Risk fuse</small>
                  <strong>10% bankroll cap · kill switch armed</strong>
                </div>
              </div>
              <div className="l-bars" aria-hidden="true">
                {Array.from({ length: 32 }).map((_, i) => (
                  <span key={i} style={{ animationDelay: `${(i % 8) * 160}ms`, height: `${28 + ((i * 13) % 62)}%` }} />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ---------- Proof ---------- */}
        <section className="l-section">
          <div className="l-proof">
            <div className="l-proof-card">
              <span className="l-kicker">Why Prospera exists</span>
              <h3>
                Most people do not need more indicators. They need a capital{" "}
                <span className="l-serif-grad">operating system.</span>
              </h3>
              <p>
                Markets are the raw material. Bots are the labor. Risk controls are the constitution.
                The demo desk proves the discipline in public, on live data, before a single real order is placed.
              </p>
            </div>
            <div className="l-proof-card">
              <span className="l-kicker">Custody model</span>
              <strong className="l-big">User-owned venues</strong>
              <p>Funds remain in the connected account. Prospera coordinates decisions and execution permissions.</p>
            </div>
            <div className="l-proof-card">
              <span className="l-kicker">Verification model</span>
              <strong className="l-big">Nothing on trust</strong>
              <p>Settlements are recomputed server-side from real candle closes. Every stat traces to the ledger.</p>
            </div>
          </div>
        </section>

        {/* ---------- Pricing ---------- */}
        <section id="pricing" className="l-section">
          <div className="l-section-head">
            <div className="l-kicker">Simple launch tiers</div>
            <h2>
              Start with observation. Graduate to <span className="l-serif-grad">autonomous deployment.</span>
            </h2>
          </div>
          <div className="l-pricing">
            {pricing.map(plan => (
              <article className={`l-price-card ${plan.featured ? "featured" : ""}`} key={plan.tier}>
                <span className="l-kicker">{plan.tier} · {plan.level}</span>
                <div className="l-price-line">
                  <strong>{plan.price}</strong>
                  <small>{plan.note}</small>
                </div>
                <ul>
                  {plan.perks.map(perk => (
                    <li key={perk}>{perk}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
          <p style={{ margin: "26px auto 0", maxWidth: 760, textAlign: "center", fontSize: 12.5, lineHeight: 1.7, color: "var(--faint)" }}>
            Daily ceilings are limits at which a lane stops trading for the day, not projected or promised returns.
            A lane that reaches its ceiling pauses until the 00:00 UTC roll; one that drops 15% pauses for 24 hours.
            Reaching a ceiling is never guaranteed, and capital is at risk — demo and past performance do not indicate future results.
          </p>
        </section>

        {/* ---------- Launch ---------- */}
        <section className="l-section">
          <div className="l-launch">
            <div>
              <div className="l-kicker">Private launch</div>
              <h2 style={{ margin: "16px 0 0", fontSize: "clamp(32px, 3.8vw, 50px)", lineHeight: 1.06, letterSpacing: "-0.03em" }}>
                Bring your capital. Prospera brings the{" "}
                <span className="l-serif-grad">autonomous infrastructure.</span>
              </h2>
              <p style={{ margin: "20px 0 0", fontSize: 15.5, lineHeight: 1.75, color: "var(--dim)", maxWidth: 460 }}>
                Join the first cohort of builders, allocators, and operators shaping bot-powered capital
                deployment before the public marketplace opens.
              </p>
              <p className="l-risk-note">
                Trading involves risk and can result in loss. Prospera is infrastructure and automation
                software, not a promise of returns or financial advice. Demo results are paper-traded.
              </p>
            </div>
            <WaitlistForm />
          </div>
        </section>

        {/* ---------- Footer ---------- */}
        <footer className="l-footer">
          <span className="l-kicker">Prospera · Wealth Automation Cloud</span>
          <span className="l-kicker">Feed: Hyperliquid L1 · Settlement: server-verified · Demo: watch-only</span>
        </footer>
      </div>
    </main>
  );
}
