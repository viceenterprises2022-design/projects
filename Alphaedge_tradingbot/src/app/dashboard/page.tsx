'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Shield, 
  ShieldAlert, 
  Activity, 
  Plus, 
  RefreshCw, 
  Play, 
  Pause, 
  AlertTriangle, 
  TrendingUp, 
  Coins, 
  Lock, 
  FileText,
  AlertOctagon
} from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Exchange Connection Form
  const [apiKey, setApiKey] = useState('');
  const [submittingConnection, setSubmittingConnection] = useState(false);

  // Bot Instance Form
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedConnection, setSelectedConnection] = useState('');
  const [riskCeiling, setRiskCeiling] = useState('5.0');
  const [maxNotional, setMaxNotional] = useState('1000');
  const [botMode, setBotMode] = useState<'paper' | 'live'>('paper');
  const [submittingInstance, setSubmittingInstance] = useState(false);

  // Webhook Simulator state
  const [simulatingSignal, setSimulatingSignal] = useState(false);

  // Fetch all dashboard data
  const fetchData = async () => {
    try {
      const res = await fetch('/api/dashboard/info');
      if (!res.ok) throw new Error('Failed to fetch dashboard data');
      const json = await res.json();
      setData(json);
      
      // Auto select first template and connection if available
      if (json.botTemplates?.length > 0 && !selectedTemplate) {
        setSelectedTemplate(json.botTemplates[0].id);
      }
      if (json.exchangeConnections?.length > 0 && !selectedConnection) {
        setSelectedConnection(json.exchangeConnections[0].id);
      }
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: err.message || 'Error loading dashboard' });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  // Add Exchange Connection
  const handleAddConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey) return;
    setSubmittingConnection(true);
    setMessage(null);

    try {
      const res = await fetch('/api/dashboard/connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exchange: 'hyperliquid', apiKey })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to add connection');
      
      setMessage({ type: 'success', text: 'Hyperliquid API key encrypted and saved securely!' });
      setApiKey('');
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error saving connection' });
    } finally {
      setSubmittingConnection(false);
    }
  };

  // Create Bot Instance
  const handleCreateInstance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTemplate || !selectedConnection) {
      setMessage({ type: 'error', text: 'Select template and exchange connection' });
      return;
    }
    setSubmittingInstance(true);
    setMessage(null);

    try {
      const res = await fetch('/api/dashboard/instances', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          botTemplateId: selectedTemplate,
          exchangeConnectionId: selectedConnection,
          mode: botMode,
          riskCeilingPct: parseFloat(riskCeiling),
          maxNotional: parseFloat(maxNotional)
        })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to create bot instance');
      
      setMessage({ type: 'success', text: 'Bot instance created and activated!' });
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error creating instance' });
    } finally {
      setSubmittingInstance(false);
    }
  };

  // Toggle Bot Status (Pause/Active/Kill Switch)
  const handleToggleBotStatus = async (instanceId: string, currentStatus: string, action: 'pause' | 'resume' | 'kill') => {
    setMessage(null);
    let nextStatus = 'active';
    if (action === 'pause') nextStatus = 'paused';
    if (action === 'kill') nextStatus = 'kill_switched';

    try {
      const res = await fetch('/api/dashboard/instances', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instanceId, status: nextStatus })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to update bot state');
      
      setMessage({ type: 'success', text: `Bot instance successfully set to ${nextStatus}!` });
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error updating status' });
    }
  };

  // Simulate Webhook Signal
  const handleSimulateSignal = async (botCode: string, direction: 'LONG' | 'SHORT' | 'EXIT', price: number) => {
    setSimulatingSignal(true);
    setMessage(null);
    try {
      const res = await fetch('/api/dashboard/mock-signal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ botCode, direction, price })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Signal execution failed');

      if (json.executions?.some((e: any) => e.status === 'rejected')) {
        const rejection = json.executions.find((e: any) => e.status === 'rejected');
        setMessage({ type: 'error', text: `Signal received but execution blocked: ${rejection.reason}` });
      } else {
        setMessage({ type: 'success', text: `Signal executed! Processed ${json.processedInstances} instances.` });
      }
      await fetchData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Error simulating webhook' });
    } finally {
      setSimulatingSignal(false);
    }
  };

  if (loading) {
    return (
      <div style={styles.centeredContainer}>
        <div className="ambient-field" />
        <div className="noise-layer" />
        <div style={styles.loader}>
          <RefreshCw style={styles.spinIcon} size={40} />
          <p style={{ marginTop: '16px', color: 'rgba(239, 246, 255, 0.66)' }}>Decrypted vault... Syncing with Hyperliquid L1...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div className="ambient-field" />
      <div className="noise-layer" />
      {/* Top Glassmorphic Navigation */}
      <header style={styles.header}>
        <div style={styles.logoRow}>
          <Link href="/" className="brand-lockup" style={{ fontSize: '1.2rem', fontWeight: 800, textDecoration: 'none', gap: '10px', display: 'flex', alignItems: 'center' }}>
            <span className="brand-mark" style={{ display: 'grid', placeItems: 'center', width: '32px', height: '32px', borderRadius: '12px', color: '#051016', background: 'conic-gradient(from 160deg, #58f0ff, #bfff6a, #9d7dff, #58f0ff)', boxShadow: '0 0 20px rgba(88, 240, 255, 0.25)', fontWeight: 'bold', fontSize: '0.9rem' }}>P</span>
            <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', color: '#fff', lineHeight: 1 }}>
              Prospera
              <small style={{ fontSize: '0.5rem', letterSpacing: '0.12em', color: 'rgba(239, 246, 255, 0.56)', marginTop: '2px', fontWeight: 700 }}>WEALTH AUTOMATION DESK</small>
            </span>
          </Link>
          <span style={styles.divider}>/</span>
          <span style={styles.panelTitle}>Trading Desk</span>
        </div>
        <div style={styles.headerRight}>
          {data?.ledgerValid ? (
            <div style={styles.ledgerBadgeVerified}>
              <Shield size={14} /> LEDGER INTEGRITY: SECURE
            </div>
          ) : (
            <div style={styles.ledgerBadgeCompromised}>
              <ShieldAlert size={14} /> LEDGER TAMPERED DETECTED
            </div>
          )}
          <button style={styles.refreshButton} onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw size={14} className={refreshing ? 'spin-icon' : ''} style={refreshing ? styles.spinAnimation : {}} />
            {refreshing ? 'Syncing...' : 'Sync'}
          </button>
        </div>
      </header>

      <div style={styles.dashboardLayout}>
        {/* Status / Message Banner */}
        {message && (
          <div style={message.type === 'success' ? styles.bannerSuccess : styles.bannerError}>
            {message.type === 'success' ? <Shield size={18} /> : <AlertOctagon size={18} />}
            <span>{message.text}</span>
          </div>
        )}

        {/* Top Analytics row */}
        <section style={styles.analyticsRow}>
          <div style={styles.analyticCard}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>USDC EQUITY</span>
              <Coins size={16} style={{ color: '#58f0ff' }} />
            </div>
            <div style={styles.cardValue}>${data?.balances?.equity?.toFixed(2)}</div>
            <div style={styles.cardSubText}>Available: ${data?.balances?.available?.toFixed(2)}</div>
          </div>

          <div style={styles.analyticCard}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>WIN RATE</span>
              <TrendingUp size={16} style={{ color: '#34d399' }} />
            </div>
            <div style={styles.cardValue}>{(data?.aiMetrics?.winRate * 100).toFixed(0)}%</div>
            <div style={styles.cardSubText}>Sharpe Ratio: {data?.aiMetrics?.sharpeRatio?.toFixed(2)}</div>
          </div>

          <div style={styles.analyticCard}>
            <div style={styles.cardHeader}>
              <span style={styles.cardTitle}>EST. PROFIT</span>
              <Activity size={16} style={{ color: '#c084fc' }} />
            </div>
            <div style={styles.cardValue} className={data?.aiMetrics?.totalProfit >= 0 ? 'text-green' : 'text-red'}>
              ${data?.aiMetrics?.totalProfit?.toFixed(2)}
            </div>
            <div style={styles.cardSubText}>Last 30 days execution</div>
          </div>
        </section>

        {/* AI Advisory Panel */}
        <section style={styles.advisoryCard}>
          <div style={styles.advisoryHeader}>
            <Shield size={18} style={{ color: '#9d7dff' }} />
            <span style={styles.advisoryTitle}>Prospera AI Risk Advisory</span>
          </div>
          <p style={styles.advisoryBody}>{data?.aiMetrics?.advisoryText}</p>
        </section>

        {/* Middle Interactive Grid */}
        <div style={styles.gridTwoCol}>
          {/* Column Left: Bot Config, Key Management & Webhook Simulator */}
          <div style={styles.gridCol}>
            {/* API Key Connection */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Lock size={16} style={{ color: '#f87171' }} /> Connect Hyperliquid Account</h2>
              <form onSubmit={handleAddConnection} style={styles.form}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Hyperliquid API/Private Wallet Key</label>
                  <input
                    type="password"
                    placeholder="Enter wallet address or private key"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    style={styles.input}
                    required
                  />
                  <small style={styles.helperText}>Plaintext keys are immediately encrypted in-memory and stored using AES-256-GCM envelope protection.</small>
                </div>
                <button type="submit" style={styles.buttonAction} disabled={submittingConnection}>
                  {submittingConnection ? 'Saving encrypted key...' : 'Connect Exchange Key'}
                </button>
              </form>

              {/* Connected keys list */}
              {data?.exchangeConnections?.length > 0 && (
                <div style={styles.connectionList}>
                  <h4 style={styles.subTitle}>Active Connections</h4>
                  {data.exchangeConnections.map((c: any) => (
                    <div key={c.id} style={styles.connectionRow}>
                      <div style={styles.connInfo}>
                        <span style={styles.connLogo}>HL</span>
                        <div>
                          <div style={styles.connName}>{c.exchange.toUpperCase()} (user_1)</div>
                          <div style={styles.connSub}>IV Tag: {c.encryptionTag.substring(0, 8)}...</div>
                        </div>
                      </div>
                      <span style={styles.statusIndicatorGreen}>ACTIVE</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Deploy new bot */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Plus size={16} style={{ color: '#3b82f6' }} /> Deploy Bot Instance</h2>
              <form onSubmit={handleCreateInstance} style={styles.form}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Select Bot Strategy Template</label>
                  <select 
                    value={selectedTemplate} 
                    onChange={(e) => setSelectedTemplate(e.target.value)}
                    style={styles.select}
                  >
                    {data?.botTemplates?.map((t: any) => (
                      <option key={t.id} value={t.id}>
                        {t.code} ({t.assetClass}) - {t.status === 'live' ? 'LIVE' : 'ASSAY'}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={styles.formGroup}>
                  <label style={styles.label}>Select Connected Exchange Key</label>
                  <select
                    value={selectedConnection}
                    onChange={(e) => setSelectedConnection(e.target.value)}
                    style={styles.select}
                  >
                    {data?.exchangeConnections?.length === 0 ? (
                      <option value="">No active exchange key connected</option>
                    ) : (
                      data?.exchangeConnections?.map((c: any) => (
                        <option key={c.id} value={c.id}>
                          {c.exchange.toUpperCase()} ({c.id.substring(0, 8)}...)
                        </option>
                      ))
                    )}
                  </select>
                </div>

                <div style={styles.formGrid}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Risk Ceiling %</label>
                    <input
                      type="number"
                      step="0.1"
                      value={riskCeiling}
                      onChange={(e) => setRiskCeiling(e.target.value)}
                      style={styles.input}
                      required
                    />
                  </div>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Max Notional ($)</label>
                    <input
                      type="number"
                      value={maxNotional}
                      onChange={(e) => setMaxNotional(e.target.value)}
                      style={styles.input}
                      required
                    />
                  </div>
                </div>

                <div style={styles.formGroup}>
                  <label style={styles.label}>Execution Mode</label>
                  <div style={styles.radioRow}>
                    <label style={styles.radioLabel}>
                      <input
                        type="radio"
                        name="mode"
                        checked={botMode === 'paper'}
                        onChange={() => setBotMode('paper')}
                        style={styles.radio}
                      />
                      Paper Trading
                    </label>
                    <label style={styles.radioLabel}>
                      <input
                        type="radio"
                        name="mode"
                        checked={botMode === 'live'}
                        onChange={() => setBotMode('live')}
                        style={styles.radio}
                      />
                      Live Execution
                    </label>
                  </div>
                </div>

                <button 
                  type="submit" 
                  style={styles.buttonAction} 
                  disabled={submittingInstance || data?.exchangeConnections?.length === 0}
                >
                  {submittingInstance ? 'Deploying...' : 'Deploy Active Bot'}
                </button>
              </form>
            </div>

            {/* Signal Simulator */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Activity size={16} style={{ color: '#fbbf24' }} /> Webhook Signal Simulator</h2>
              <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '16px' }}>
                Simulate TradingView alerts sending buy/sell webhook signals directly to our parser:
              </p>
              
              <div style={styles.simulatorGrid}>
                {data?.botTemplates?.map((tmpl: any) => (
                  <div key={tmpl.id} style={styles.simCard}>
                    <div style={styles.simTitle}>
                      <span>{tmpl.code}</span>
                      <span style={tmpl.status === 'live' ? styles.statusGreen : styles.statusAmber}>
                        {tmpl.status.toUpperCase()}
                      </span>
                    </div>
                    <div style={styles.simActions}>
                      <button 
                        style={styles.simButtonLong} 
                        onClick={() => handleSimulateSignal(tmpl.code, 'LONG', tmpl.assetClass === 'BTC' ? 62450.00 : tmpl.assetClass === 'ETH' ? 3420.00 : 2350.00)}
                        disabled={simulatingSignal}
                      >
                        LONG Signal
                      </button>
                      <button 
                        style={styles.simButtonShort} 
                        onClick={() => handleSimulateSignal(tmpl.code, 'SHORT', tmpl.assetClass === 'BTC' ? 62450.00 : tmpl.assetClass === 'ETH' ? 3420.00 : 2350.00)}
                        disabled={simulatingSignal}
                      >
                        SHORT Signal
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Column Right: Active Bots, Trade Ledger (Journal) & Risk Audit logs */}
          <div style={styles.gridCol}>
            {/* Active Bots list */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Activity size={16} style={{ color: '#34d399' }} /> Active Bot Deployments</h2>
              {data?.botInstances?.length === 0 ? (
                <div style={styles.emptyState}>No active bot instances deployed. Create one on the left.</div>
              ) : (
                <div style={styles.botGrid}>
                  {data.botInstances.map((bot: any) => {
                    const templateCode = data.botTemplates.find((t: any) => t.id === bot.botTemplateId)?.code || 'Unknown';
                    
                    return (
                      <div key={bot.id} style={styles.botCard}>
                        <div style={styles.botCardHeader}>
                          <div>
                            <span style={styles.botCodeName}>{templateCode}</span>
                            <span style={bot.mode === 'live' ? styles.badgeLive : styles.badgePaper}>
                              {bot.mode.toUpperCase()}
                            </span>
                          </div>
                          <span style={
                            bot.status === 'active' ? styles.botStatusActive : 
                            bot.status === 'paused' ? styles.botStatusPaused : 
                            styles.botStatusKilled
                          }>
                            {bot.status.toUpperCase()}
                          </span>
                        </div>
                        <div style={styles.botCardBody}>
                          <div>Risk Ceiling: {bot.riskCeilingPct}%</div>
                          <div>Max Notional: ${bot.maxNotional}</div>
                        </div>
                        <div style={styles.botCardActions}>
                          {bot.status === 'active' && (
                            <button 
                              style={styles.botButtonPause}
                              onClick={() => handleToggleBotStatus(bot.id, bot.status, 'pause')}
                            >
                              <Pause size={12} /> Pause
                            </button>
                          )}
                          {bot.status === 'paused' && (
                            <button 
                              style={styles.botButtonResume}
                              onClick={() => handleToggleBotStatus(bot.id, bot.status, 'resume')}
                            >
                              <Play size={12} /> Resume
                            </button>
                          )}
                          {bot.status !== 'kill_switched' && (
                            <button 
                              style={styles.botButtonKill}
                              onClick={() => handleToggleBotStatus(bot.id, bot.status, 'kill')}
                            >
                              <AlertTriangle size={12} /> Kill Switch
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Position state */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><Coins size={16} style={{ color: '#fbbf24' }} /> Hyperliquid Positions</h2>
              {data?.positions?.length === 0 ? (
                <div style={styles.emptyState}>No open positions currently held.</div>
              ) : (
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Coin</th>
                      <th style={styles.th}>Size</th>
                      <th style={styles.th}>Entry Price</th>
                      <th style={styles.th}>Unrealized PnL</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.positions.map((pos: any, idx: number) => (
                      <tr key={idx} style={styles.tr}>
                        <td style={styles.td}>{pos.coin}</td>
                        <td style={pos.szi >= 0 ? styles.tdGreen : styles.tdRed}>
                          {pos.szi > 0 ? `+${pos.szi}` : pos.szi}
                        </td>
                        <td style={styles.td}>${pos.entryPx.toFixed(2)}</td>
                        <td style={pos.unrealizedPnl >= 0 ? styles.tdGreen : styles.tdRed}>
                          ${pos.unrealizedPnl.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Trade Journal (Ledger Entries) */}
            <div style={styles.panelCard}>
              <h2 style={styles.panelHeader}><FileText size={16} style={{ color: '#c084fc' }} /> Cryptographic Trade Ledger</h2>
              <div style={styles.journalContainer}>
                {data?.orders?.length === 0 ? (
                  <div style={styles.emptyState}>No historical executions recorded.</div>
                ) : (
                  <div style={styles.timeline}>
                    {data.orders.map((ord: any) => (
                      <div key={ord.id} style={styles.timelineItem}>
                        <div style={styles.timelineHeader}>
                          <span style={ord.side === 'buy' ? styles.buyTag : styles.sellTag}>
                            {ord.side.toUpperCase()}
                          </span>
                          <span style={styles.timelineTime}>
                            {new Date(ord.submittedAt).toLocaleTimeString()}
                          </span>
                        </div>
                        <div style={styles.timelineBody}>
                          <span>Qty: {ord.qty.toFixed(4)} @ ${ord.price.toFixed(2)}</span>
                          <span style={ord.status === 'filled' ? styles.statusGreen : styles.statusRed}>
                            {ord.status.toUpperCase()}
                          </span>
                        </div>
                        <div style={styles.timelineHash}>
                          Hash: <code>{ord.id}</code>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Risk Audits list */}
            {data?.riskEvents?.length > 0 && (
              <div style={styles.panelCard}>
                <h2 style={styles.panelHeader}><AlertOctagon size={16} style={{ color: '#f87171' }} /> Risk Audit Logs</h2>
                <div style={styles.auditContainer}>
                  {data.riskEvents.map((evt: any) => (
                    <div key={evt.id} style={styles.auditRow}>
                      <div style={styles.auditTime}>
                        {new Date(evt.timestamp).toLocaleTimeString()}
                      </div>
                      <div style={styles.auditDetail}>
                        <strong>{evt.type.toUpperCase()}:</strong> {evt.detail}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    backgroundColor: '#050711',
    color: '#ffffff',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    zIndex: 1,
  },
  centeredContainer: {
    backgroundColor: '#050711',
    color: '#ffffff',
    minHeight: '100vh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    zIndex: 1,
  },
  loader: {
    textAlign: 'center',
    position: 'relative',
    zIndex: 2,
  },
  spinIcon: {
    animation: 'spin 1.5s linear infinite',
    color: '#58f0ff',
  },
  spinAnimation: {
    animation: 'spin 1s linear infinite',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
    backgroundColor: 'rgba(5, 7, 17, 0.65)',
    backdropFilter: 'blur(20px)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  logoRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  logoLink: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#ffffff',
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  logoSymbol: {
    color: '#58f0ff',
  },
  divider: {
    color: 'rgba(255, 255, 255, 0.14)',
    fontWeight: 300,
  },
  panelTitle: {
    fontSize: '14px',
    color: 'rgba(239, 246, 255, 0.82)',
    fontWeight: 500,
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  ledgerBadgeVerified: {
    backgroundColor: 'rgba(191, 255, 106, 0.1)',
    border: '1px solid rgba(191, 255, 106, 0.3)',
    color: '#bfff6a',
    fontSize: '12px',
    fontWeight: 600,
    padding: '6px 12px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  ledgerBadgeCompromised: {
    backgroundColor: 'rgba(255, 111, 179, 0.1)',
    border: '1px solid rgba(255, 111, 179, 0.3)',
    color: '#ff6fb3',
    fontSize: '12px',
    fontWeight: 600,
    padding: '6px 12px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  refreshButton: {
    backgroundColor: 'transparent',
    border: '1px solid rgba(255, 255, 255, 0.14)',
    color: 'rgba(239, 246, 255, 0.66)',
    padding: '6px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 500,
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    transition: 'all 0.2s',
  },
  dashboardLayout: {
    flex: 1,
    padding: '24px',
    maxWidth: '1400px',
    margin: '0 auto',
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    position: 'relative',
    zIndex: 2,
  },
  bannerSuccess: {
    backgroundColor: 'rgba(191, 255, 106, 0.1)',
    border: '1px solid rgba(191, 255, 106, 0.3)',
    color: '#bfff6a',
    padding: '12px 16px',
    borderRadius: '12px',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  bannerError: {
    backgroundColor: 'rgba(255, 111, 179, 0.1)',
    border: '1px solid rgba(255, 111, 179, 0.3)',
    color: '#ff6fb3',
    padding: '12px 16px',
    borderRadius: '12px',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  analyticsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: '16px',
  },
  analyticCard: {
    background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.025))',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '24px',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    backdropFilter: 'blur(20px)',
    boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08)',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: '11px',
    fontWeight: 600,
    color: 'rgba(239, 246, 255, 0.54)',
    letterSpacing: '1px',
  },
  cardValue: {
    fontSize: '28px',
    fontWeight: 'bold',
  },
  cardSubText: {
    fontSize: '12px',
    color: 'rgba(239, 246, 255, 0.66)',
  },
  advisoryCard: {
    backgroundColor: 'rgba(157, 125, 255, 0.06)',
    border: '1px solid rgba(157, 125, 255, 0.22)',
    borderRadius: '20px',
    padding: '16px 20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    backdropFilter: 'blur(20px)',
  },
  advisoryHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  advisoryTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#9d7dff',
  },
  advisoryBody: {
    fontSize: '13px',
    color: 'rgba(239, 246, 255, 0.7)',
    lineHeight: 1.5,
  },
  gridTwoCol: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
    gap: '24px',
  },
  gridCol: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  panelCard: {
    background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.025))',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '24px',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    backdropFilter: 'blur(20px)',
    boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08)',
  },
  panelHeader: {
    fontSize: '16px',
    fontWeight: 600,
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.14)',
    paddingBottom: '12px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  formGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px',
  },
  label: {
    fontSize: '12px',
    fontWeight: 500,
    color: 'rgba(239, 246, 255, 0.66)',
  },
  input: {
    backgroundColor: 'rgba(5, 7, 17, 0.64)',
    border: '1px solid rgba(255, 255, 255, 0.14)',
    color: '#ffffff',
    padding: '12px 14px',
    borderRadius: '14px',
    fontSize: '14px',
    outline: 'none',
  },
  select: {
    backgroundColor: 'rgba(5, 7, 17, 0.64)',
    border: '1px solid rgba(255, 255, 255, 0.14)',
    color: '#ffffff',
    padding: '12px 14px',
    borderRadius: '14px',
    fontSize: '14px',
    outline: 'none',
  },
  helperText: {
    fontSize: '11px',
    color: 'rgba(239, 246, 255, 0.5)',
  },
  buttonAction: {
    background: 'linear-gradient(135deg, #58f0ff, #bfff6a)',
    color: '#051016',
    border: 'none',
    padding: '14px 22px',
    borderRadius: '16px',
    fontWeight: 820,
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'all 0.2s',
    boxShadow: '0 8px 24px rgba(88, 240, 255, 0.2)',
    letterSpacing: '-0.02em',
  },
  radioRow: {
    display: 'flex',
    gap: '16px',
    marginTop: '4px',
  },
  radioLabel: {
    fontSize: '13px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    cursor: 'pointer',
  },
  radio: {
    accentColor: '#58f0ff',
  },
  connectionList: {
    marginTop: '20px',
    borderTop: '1px solid rgba(255, 255, 255, 0.14)',
    paddingTop: '16px',
  },
  subTitle: {
    fontSize: '13px',
    color: 'rgba(239, 246, 255, 0.5)',
    marginBottom: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  connectionRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(5, 7, 17, 0.5)',
    padding: '12px',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.12)',
  },
  connInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  connLogo: {
    backgroundColor: '#58f0ff',
    color: '#051016',
    width: '28px',
    height: '28px',
    borderRadius: '50px',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    fontSize: '12px',
    fontWeight: 'bold',
  },
  connName: {
    fontSize: '13px',
    fontWeight: 600,
  },
  connSub: {
    fontSize: '11px',
    color: 'rgba(239, 246, 255, 0.5)',
  },
  statusIndicatorGreen: {
    fontSize: '10px',
    fontWeight: 600,
    color: '#bfff6a',
    backgroundColor: 'rgba(191, 255, 106, 0.1)',
    padding: '2px 6px',
    borderRadius: '4px',
  },
  simulatorGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  simCard: {
    backgroundColor: 'rgba(5, 7, 17, 0.5)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '16px',
    padding: '14px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  simTitle: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    fontWeight: 600,
    fontSize: '14px',
  },
  statusGreen: {
    fontSize: '10px',
    color: '#bfff6a',
    fontWeight: 600,
  },
  statusAmber: {
    fontSize: '10px',
    color: '#ffd166',
    fontWeight: 600,
  },
  simActions: {
    display: 'flex',
    gap: '8px',
  },
  simButtonLong: {
    backgroundColor: 'rgba(191, 255, 106, 0.12)',
    border: '1px solid rgba(191, 255, 106, 0.3)',
    color: '#bfff6a',
    padding: '6px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  simButtonShort: {
    backgroundColor: 'rgba(255, 111, 179, 0.12)',
    border: '1px solid rgba(255, 111, 179, 0.3)',
    color: '#ff6fb3',
    padding: '6px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  emptyState: {
    textAlign: 'center',
    color: 'rgba(239, 246, 255, 0.5)',
    padding: '24px 0',
    fontSize: '14px',
  },
  botGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  botCard: {
    backgroundColor: 'rgba(5, 7, 17, 0.5)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    borderRadius: '20px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  botCardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  botCodeName: {
    fontSize: '14px',
    fontWeight: 'bold',
    marginRight: '8px',
  },
  badgeLive: {
    backgroundColor: 'rgba(191, 255, 106, 0.15)',
    color: '#bfff6a',
    fontSize: '9px',
    fontWeight: 600,
    padding: '2px 6px',
    borderRadius: '4px',
  },
  badgePaper: {
    backgroundColor: 'rgba(157, 125, 255, 0.15)',
    color: '#9d7dff',
    fontSize: '9px',
    fontWeight: 600,
    padding: '2px 6px',
    borderRadius: '4px',
  },
  botStatusActive: {
    fontSize: '11px',
    fontWeight: 600,
    color: '#bfff6a',
    padding: '4px 8px',
    borderRadius: '20px',
    backgroundColor: 'rgba(191, 255, 106, 0.1)',
  },
  botStatusPaused: {
    fontSize: '11px',
    fontWeight: 600,
    color: '#ffd166',
    padding: '4px 8px',
    borderRadius: '20px',
    backgroundColor: 'rgba(255, 209, 102, 0.1)',
  },
  botStatusKilled: {
    fontSize: '11px',
    fontWeight: 600,
    color: '#ff6fb3',
    padding: '4px 8px',
    borderRadius: '20px',
    backgroundColor: 'rgba(255, 111, 179, 0.1)',
  },
  botCardBody: {
    fontSize: '12px',
    color: 'rgba(239, 246, 255, 0.66)',
    display: 'flex',
    gap: '16px',
  },
  botCardActions: {
    display: 'flex',
    gap: '8px',
    marginTop: '4px',
  },
  botButtonPause: {
    backgroundColor: 'transparent',
    border: '1px solid #ffd166',
    color: '#ffd166',
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '11px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  botButtonResume: {
    backgroundColor: 'transparent',
    border: '1px solid #bfff6a',
    color: '#bfff6a',
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '11px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  botButtonKill: {
    backgroundColor: 'transparent',
    border: '1px solid #ff6fb3',
    color: '#ff6fb3',
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '11px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '13px',
  },
  th: {
    textAlign: 'left',
    color: 'rgba(239, 246, 255, 0.54)',
    fontWeight: 600,
    padding: '8px 12px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.14)',
  },
  tr: {
    borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
  },
  td: {
    padding: '10px 12px',
  },
  tdGreen: {
    padding: '10px 12px',
    color: '#bfff6a',
    fontWeight: 500,
  },
  tdRed: {
    padding: '10px 12px',
    color: '#ff6fb3',
    fontWeight: 500,
  },
  journalContainer: {
    maxHeight: '300px',
    overflowY: 'auto',
  },
  timeline: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  timelineItem: {
    borderLeft: '2px solid rgba(255, 255, 255, 0.14)',
    paddingLeft: '16px',
    marginLeft: '6px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  timelineHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  buyTag: {
    color: '#bfff6a',
    fontSize: '11px',
    fontWeight: 'bold',
  },
  sellTag: {
    color: '#ff6fb3',
    fontSize: '11px',
    fontWeight: 'bold',
  },
  timelineTime: {
    fontSize: '11px',
    color: 'rgba(239, 246, 255, 0.5)',
  },
  timelineBody: {
    fontSize: '13px',
    display: 'flex',
    justifyContent: 'space-between',
  },
  timelineHash: {
    fontSize: '10px',
    color: 'rgba(239, 246, 255, 0.5)',
  },
  auditContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    maxHeight: '200px',
    overflowY: 'auto',
  },
  auditRow: {
    backgroundColor: 'rgba(5, 7, 17, 0.5)',
    borderLeft: '3px solid #ff6fb3',
    padding: '10px 12px',
    borderRadius: '12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  auditTime: {
    fontSize: '10px',
    color: 'rgba(239, 246, 255, 0.5)',
  },
  auditDetail: {
    fontSize: '12px',
    color: '#ffffff',
  },
};

