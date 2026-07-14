import { db } from "@/db";
import { earlyAccessLeads } from "@/db/schema";
import { sql } from "drizzle-orm";
import { WaitlistForm } from "./waitlist-form";

export const dynamic = "force-dynamic";

const wealthLoops = [
  "market regime scanner",
  "risk-budget allocator",
  "execution swarm",
  "portfolio memory",
];

const botCards = [
  {
    name: "Pulse",
    mandate: "Momentum compounding",
    markets: "Crypto · FX · Index futures",
    accent: "cyan",
    stat: "+18.4%",
  },
  {
    name: "Harbor",
    mandate: "Downside-aware grid",
    markets: "BTC · ETH · Gold · Oil",
    accent: "violet",
    stat: "0.62x",
  },
  {
    name: "Atlas",
    mandate: "Multi-asset rotation",
    markets: "Commodities · Crypto · ETFs",
    accent: "lime",
    stat: "12 lanes",
  },
];

const features = [
  {
    eyebrow: "01 / Control",
    title: "Your capital stays where you custody it.",
    body: "Connect exchange or broker APIs with trade-only permissions. Prospera never asks for withdrawal rights, and every bot can be paused, capped, or unwound from one command center.",
  },
  {
    eyebrow: "02 / Intelligence",
    title: "A wealth engine, not another chart screen.",
    body: "Bots translate volatility, liquidity, macro pressure, and portfolio exposure into executable playbooks that are sized to your risk budget.",
  },
  {
    eyebrow: "03 / Expansion",
    title: "Built for crypto today, commodities tomorrow, everything next.",
    body: "Launch with digital assets and liquid macro venues, then expand into metals, energy, equities, and custom private strategies as new connectors go live.",
  },
];

const pricing = [
  {
    tier: "Seed",
    price: "0%",
    note: "for exploration",
    perks: ["Simulated bot runs", "Strategy marketplace preview", "Capital map dashboard"],
  },
  {
    tier: "Builder",
    price: "1.2%",
    note: "annual platform access",
    perks: ["Live bot deployment", "Risk guardrails", "Exchange connectors", "Private telemetry"],
    featured: true,
  },
  {
    tier: "Sovereign",
    price: "Custom",
    note: "for teams and allocators",
    perks: ["White-glove onboarding", "Custom mandates", "Multi-account controls", "Research desk access"],
  },
];

async function getLaunchCount() {
  try {
    const [row] = await db.select({ total: sql<number>`count(*)::int` }).from(earlyAccessLeads);
    return Number(row?.total ?? 0);
  } catch {
    return 0;
  }
}

function SignalBars() {
  return (
    <div className="signal-bars" aria-hidden="true">
      {Array.from({ length: 34 }).map((_, index) => (
        <span key={index} />
      ))}
    </div>
  );
}

function CommandDeck() {
  return (
    <div className="deck-shell">
      <div className="deck-orbit deck-orbit-one" />
      <div className="deck-orbit deck-orbit-two" />
      <div className="deck-topline">
        <span className="live-dot" />
        <span>Prospera Mesh / Live Simulation</span>
        <span>Risk locked</span>
      </div>

      <div className="wealth-core">
        <div className="core-ring" />
        <div className="core-inner">
          <span>Capital OS</span>
          <strong>87</strong>
          <small>autonomy score</small>
        </div>
      </div>

      <div className="bot-stack">
        {botCards.map((bot) => (
          <article className={`bot-card bot-${bot.accent}`} key={bot.name}>
            <div>
              <span>{bot.name}</span>
              <strong>{bot.mandate}</strong>
            </div>
            <p>{bot.markets}</p>
            <em>{bot.stat}</em>
          </article>
        ))}
      </div>

      <div className="risk-console">
        <div>
          <span>Drawdown fuse</span>
          <strong>armed</strong>
        </div>
        <div>
          <span>Trade permissions</span>
          <strong>no withdrawals</strong>
        </div>
        <div>
          <span>Venue custody</span>
          <strong>user-owned</strong>
        </div>
      </div>
    </div>
  );
}

export default async function HomePage() {
  const launchCount = await getLaunchCount();
  const visibleLaunchCount = Math.max(312, launchCount + 312);

  return (
    <main className="min-h-screen overflow-hidden bg-[#050711] text-white">
      <div className="ambient-field" />
      <div className="noise-layer" />

      <nav className="site-nav">
        <a href="#top" className="brand-lockup" aria-label="Prospera home">
          <span className="brand-mark">P</span>
          <span>
            Prospera
            <small>wealth automation cloud</small>
          </span>
        </a>
        <div className="nav-links" aria-label="Primary navigation">
          <a href="#engine">Engine</a>
          <a href="#bots">Bots</a>
          <a href="#pricing">Pricing</a>
          <a href="#launch">Access</a>
        </div>
        <a className="nav-cta" href="#launch">
          Open capital cockpit
        </a>
      </nav>

      <section id="top" className="hero-section">
        <div className="hero-copy">
          <div className="status-pill">
            <span className="live-dot" />
            Not Assay. Not gold-only. Built for every wealth frontier.
          </div>
          <h1>
            Turn idle capital into an <span>autonomous wealth system.</span>
          </h1>
          <p className="hero-lede">
            Prospera lets users deploy their own cash into intelligent strategy bots across crypto, commodities,
            FX, equities, and future market connectors — with trade-only API keys, transparent guardrails, and a
            command center designed for wealth creation instead of chart watching.
          </p>
          <div className="hero-actions">
            <a href="#launch" className="primary-action">
              Request private launch <span>↗</span>
            </a>
            <a href="#engine" className="secondary-action">
              See the wealth engine
            </a>
          </div>
          <div className="hero-metrics" aria-label="Platform highlights">
            <div>
              <strong>{visibleLaunchCount}</strong>
              <span>private launch requests</span>
            </div>
            <div>
              <strong>24/7</strong>
              <span>autonomous monitoring</span>
            </div>
            <div>
              <strong>0</strong>
              <span>withdrawal permissions required</span>
            </div>
          </div>
        </div>

        <div className="hero-visual" aria-label="Prospera capital command deck preview">
          <CommandDeck />
        </div>
      </section>

      <section className="ticker-ribbon" aria-label="Supported market roadmap">
        <div>
          {[
            "BTC",
            "ETH",
            "SOL",
            "GOLD",
            "OIL",
            "FX",
            "EQUITIES",
            "RATES",
            "CUSTOM BOTS",
            "RISK MESH",
          ].map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </section>

      <section id="engine" className="engine-section">
        <div className="section-kicker">Capital autonomy without surrendering control</div>
        <div className="section-heading-row">
          <h2>
            Wealth is a system. Prospera gives it an <em className="accent-serif">operating layer.</em>
          </h2>
          <p>
            Instead of building another trading terminal, Prospera turns strategies into governed bots: choose a
            mandate, define capital limits, connect your venue, and let the platform manage execution discipline.
          </p>
        </div>

        <div className="loop-grid">
          {wealthLoops.map((loop, index) => (
            <article className="loop-card" key={loop}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{loop}</h3>
              <p>
                Continuously reads market structure, account exposure, and strategy health before capital is placed
                into motion.
              </p>
            </article>
          ))}
        </div>
      </section>

      <section id="bots" className="bot-section">
        <div className="bot-copy">
          <div className="section-kicker">Bot marketplace</div>
          <h2>
            Deploy cash through bots that behave like <em className="accent-serif">mandates.</em>
          </h2>
          <p>
            Every Prospera bot ships with a thesis, capital envelope, stop logic, rebalance cadence, and clear venue
            requirements. You are not buying signals — you are configuring a wealth-building workflow.
          </p>
          <ul className="check-list">
            <li>Trade-only exchange and broker keys</li>
            <li>Per-bot capital caps, pause rules, and kill switches</li>
            <li>Transparent logs for entries, exits, rebalances, and risk events</li>
            <li>Multi-market roadmap spanning crypto, commodities, FX, equities, and custom strategies</li>
          </ul>
        </div>
        <div className="bot-lab">
          <div className="lab-header">
            <span>Bot lab</span>
            <strong>Mandate composer</strong>
          </div>
          <div className="mandate-panel">
            <div>
              <small>Objective</small>
              <strong>Compound with controlled volatility</strong>
            </div>
            <div>
              <small>Capital lane</small>
              <strong>$25,000 · user custody</strong>
            </div>
            <div>
              <small>Universe</small>
              <strong>BTC / ETH / Gold / Oil</strong>
            </div>
          </div>
          <SignalBars />
          <div className="lab-footer">
            <span>Deploy preview</span>
            <strong>12 risk checks passed</strong>
          </div>
        </div>
      </section>

      <section className="feature-strip">
        {features.map((feature) => (
          <article key={feature.title}>
            <span>{feature.eyebrow}</span>
            <h3>{feature.title}</h3>
            <p>{feature.body}</p>
          </article>
        ))}
      </section>

      <section className="proof-section">
        <div className="proof-card proof-card-large">
          <span>Why Prospera exists</span>
          <h2>
            Most people do not need more indicators. They need a capital{" "}
            <em className="accent-serif">operating system.</em>
          </h2>
          <p>
            The platform is designed around the outcome users actually care about: creating wealth over time. Markets
            are the raw material. Bots are the labor. Risk controls are the constitution.
          </p>
        </div>
        <div className="proof-card">
          <span>Custody model</span>
          <strong>User-owned venues</strong>
          <p>Funds remain in the connected account. Prospera coordinates decisions and execution permissions.</p>
        </div>
        <div className="proof-card">
          <span>Positioning</span>
          <strong>Generic by design</strong>
          <p>Not gold-branded, not crypto-only, and not locked to one strategy family.</p>
        </div>
      </section>

      <section id="pricing" className="pricing-section">
        <div className="section-kicker">Simple launch tiers</div>
        <h2>
          Start with observation. Graduate to <em className="accent-serif">autonomous deployment.</em>
        </h2>
        <div className="pricing-grid">
          {pricing.map((plan) => (
            <article className={`pricing-card ${plan.featured ? "featured" : ""}`} key={plan.tier}>
              <span>{plan.tier}</span>
              <div>
                <strong>{plan.price}</strong>
                <small>{plan.note}</small>
              </div>
              <ul>
                {plan.perks.map((perk) => (
                  <li key={perk}>{perk}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      <section className="launch-section">
        <div className="launch-copy">
          <div className="section-kicker">Private launch</div>
          <h2>
            Bring your capital. Prospera brings the{" "}
            <em className="accent-serif">autonomous wealth infrastructure.</em>
          </h2>
          <p>
            Join the first cohort of builders, allocators, and operators shaping bot-powered capital deployment before
            the public marketplace opens.
          </p>
          <p className="risk-note">
            Trading involves risk and can result in loss. Prospera is infrastructure and automation software, not a
            promise of returns or financial advice.
          </p>
        </div>
        <WaitlistForm />
      </section>
    </main>
  );
}
