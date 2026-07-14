import Link from 'next/link';

export default function Home() {
  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.logo}>
          <span style={styles.logoSymbol}>▲</span> AlphaEdge
        </div>
        <nav style={styles.nav}>
          <Link href="/dashboard" style={styles.buttonPrimary}>Enter App</Link>
        </nav>
      </header>

      <main style={styles.main}>
        <section style={styles.hero}>
          <div style={styles.badge}>Commercial SaaS Protocol v1.0</div>
          <h1 style={styles.title}>
            Automated Breakout <br />
            <span style={styles.goldText}>Execution on Hyperliquid</span>
          </h1>
          <p style={styles.subtitle}>
            A developer-first, non-custodial trading bot platform. Connect your API keys, configure risk ceilings, and execute TradingView webhook signals with sub-second latency.
          </p>
          <div style={styles.heroActions}>
            <Link href="/dashboard" style={styles.buttonLarge}>Launch Trading Dashboard</Link>
            <a href="#features" style={styles.buttonSecondary}>Read Architecture Spec</a>
          </div>
        </section>

        <section id="features" style={styles.features}>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🛡️</div>
            <h3 style={styles.featureTitle}>Non-Custodial Keys</h3>
            <p style={styles.featureText}>
              API keys are envelope-encrypted in memory using AES-256-GCM. We never custody funds; withdrawals are blocked in code.
            </p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>⚡</div>
            <h3 style={styles.featureTitle}>Critical Path Speed</h3>
            <p style={styles.featureText}>
              Zero AI in the critical trading pipeline. Execution is pure rule-based routing to maximize Hyperliquid API speed.
            </p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🔗</div>
            <h3 style={styles.featureTitle}>Hash-Chained Ledger</h3>
            <p style={styles.featureText}>
              Every signal, fill, and risk event is cryptographically hash-chained in an append-only ledger for absolute auditability.
            </p>
          </div>
        </section>
      </main>

      <footer style={styles.footer}>
        <p>AlphaEdge © 2026. Made for professional and retail crypto breakout execution.</p>
      </footer>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    backgroundColor: '#080c14',
    color: '#f1f5f9',
    overflowX: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '24px 40px',
    borderBottom: '1px solid #1f2b45',
    backdropFilter: 'blur(12px)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  logo: {
    fontSize: '20px',
    fontWeight: 'bold',
    letterSpacing: '1px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  logoSymbol: {
    color: '#fbbf24',
  },
  nav: {
    display: 'flex',
    alignItems: 'center',
  },
  buttonPrimary: {
    backgroundColor: '#fbbf24',
    color: '#080c14',
    padding: '8px 16px',
    borderRadius: '6px',
    textDecoration: 'none',
    fontWeight: 600,
    fontSize: '14px',
    transition: 'all 0.2s ease',
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '80px 24px',
    maxWidth: '1200px',
    margin: '0 auto',
    width: '100%',
  },
  hero: {
    textAlign: 'center',
    maxWidth: '800px',
    marginBottom: '80px',
  },
  badge: {
    display: 'inline-block',
    backgroundColor: '#172033',
    border: '1px solid #1f2b45',
    color: '#c084fc',
    fontSize: '12px',
    fontWeight: 600,
    padding: '6px 12px',
    borderRadius: '50px',
    marginBottom: '24px',
    letterSpacing: '0.5px',
  },
  title: {
    fontSize: '56px',
    fontWeight: 'bold',
    lineHeight: 1.15,
    marginBottom: '24px',
    letterSpacing: '-1px',
  },
  goldText: {
    background: 'linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  subtitle: {
    fontSize: '18px',
    color: '#94a3b8',
    lineHeight: 1.6,
    marginBottom: '40px',
  },
  heroActions: {
    display: 'flex',
    justifyContent: 'center',
    gap: '16px',
    flexWrap: 'wrap',
  },
  buttonLarge: {
    backgroundColor: '#fbbf24',
    color: '#080c14',
    padding: '14px 28px',
    borderRadius: '6px',
    textDecoration: 'none',
    fontWeight: 600,
    fontSize: '16px',
    transition: 'all 0.2s ease',
    boxShadow: '0 4px 14px 0 rgba(251, 191, 36, 0.3)',
  },
  buttonSecondary: {
    backgroundColor: 'transparent',
    color: '#f1f5f9',
    border: '1px solid #1f2b45',
    padding: '14px 28px',
    borderRadius: '6px',
    textDecoration: 'none',
    fontWeight: 600,
    fontSize: '16px',
    transition: 'all 0.2s ease',
  },
  features: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '24px',
    width: '100%',
  },
  featureCard: {
    backgroundColor: '#0e1524',
    border: '1px solid #1f2b45',
    borderRadius: '8px',
    padding: '32px',
    transition: 'transform 0.2s ease, border-color 0.2s ease',
    cursor: 'default',
  },
  featureIcon: {
    fontSize: '32px',
    marginBottom: '16px',
  },
  featureTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    marginBottom: '12px',
  },
  featureText: {
    color: '#94a3b8',
    fontSize: '14px',
    lineHeight: 1.5,
  },
  footer: {
    padding: '40px',
    borderTop: '1px solid #1f2b45',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '14px',
  },
};
