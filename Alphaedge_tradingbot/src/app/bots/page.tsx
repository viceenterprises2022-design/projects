import { db } from "@/db"
import { botTemplates, botInstances } from "@/db/schema"
import { subscribeToBot } from "./actions"
import { eq } from "drizzle-orm"

const SYSTEM_USER_ID = "system-user"

export default async function BotsDashboard() {
  const user = { id: SYSTEM_USER_ID, name: "AlphaEdge User", email: "user@alphaedge.ai", image: null }

  // Fetch all available bot templates
  const templates = await db.select().from(botTemplates)
  
  // Fetch user's active bot subscriptions
  const userInstances = await db.select().from(botInstances).where(eq(botInstances.userId, SYSTEM_USER_ID))
  const subscribedTemplateIds = new Set(userInstances.map(inst => inst.botTemplateId))

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#080c14', color: '#f1f5f9', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 32px', backgroundColor: '#0e1524', borderBottom: '1px solid #1f2b45' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '32px', height: '32px', backgroundColor: '#fbbf24', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: '#080c14' }}>
            AE
          </div>
          <h1 style={{ fontSize: '18px', fontWeight: 600 }}>Alphaedge Quant Hub</h1>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '14px', color: '#94a3b8' }}>{user.name}</span>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 600, marginBottom: '8px' }}>Available Quant Strategies</h2>
          <p style={{ color: '#94a3b8', fontSize: '14px' }}>Browse and subscribe to our proprietary algorithmic trading bots.</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
          {templates.map(bot => {
            const isSubscribed = subscribedTemplateIds.has(bot.id)
            
            return (
              <div key={bot.id} style={{ 
                backgroundColor: '#0e1524', 
                border: '1px solid #1f2b45', 
                borderRadius: '8px', 
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                cursor: 'default'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#f1f5f9' }}>{bot.code}</h3>
                    <span style={{ fontSize: '12px', color: '#c084fc', backgroundColor: 'rgba(192, 132, 252, 0.1)', padding: '2px 8px', borderRadius: '12px', display: 'inline-block', marginTop: '8px' }}>
                      {bot.assetClass}
                    </span>
                  </div>
                  
                  {bot.status === 'live' ? (
                    <span style={{ fontSize: '12px', color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#34d399', display: 'inline-block' }}></span>
                      LIVE
                    </span>
                  ) : (
                    <span style={{ fontSize: '12px', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#fbbf24', display: 'inline-block' }}></span>
                      IN ASSAY
                    </span>
                  )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', backgroundColor: '#080c14', padding: '12px', borderRadius: '6px' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '2px' }}>Min Win Rate</div>
                    <div style={{ fontSize: '14px', fontWeight: 500 }}>{bot.minWinRate ? `${(bot.minWinRate * 100).toFixed(1)}%` : 'N/A'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '2px' }}>Expectancy</div>
                    <div style={{ fontSize: '14px', fontWeight: 500, color: '#34d399' }}>{bot.minExpectancy ? `+${bot.minExpectancy}` : 'N/A'}</div>
                  </div>
                </div>

                <div style={{ marginTop: 'auto', paddingTop: '8px' }}>
                  {isSubscribed ? (
                    <button disabled style={{ 
                      width: '100%', 
                      padding: '10px', 
                      backgroundColor: 'rgba(52, 211, 153, 0.1)', 
                      color: '#34d399', 
                      border: '1px solid rgba(52, 211, 153, 0.2)', 
                      borderRadius: '6px',
                      fontSize: '14px',
                      fontWeight: 500,
                      cursor: 'not-allowed'
                    }}>
                      Subscribed & Deployed
                    </button>
                  ) : (
                    <form action={subscribeToBot}>
                      <input type="hidden" name="botTemplateId" value={bot.id} />
                      <button type="submit" style={{ 
                        width: '100%', 
                        padding: '10px', 
                        backgroundColor: '#fbbf24', 
                        color: '#080c14', 
                        border: 'none', 
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'opacity 0.2s'
                      }}>
                        Subscribe Bot
                      </button>
                    </form>
                  )}
                </div>
              </div>
            )
          })}
        </div>
        
        {userInstances.length > 0 && (
          <div style={{ marginTop: '48px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px' }}>Your Active Instances</h2>
            <div style={{ backgroundColor: '#0e1524', border: '1px solid #1f2b45', borderRadius: '8px', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1f2b45', backgroundColor: 'rgba(23, 32, 51, 0.5)' }}>
                    <th style={{ padding: '12px 16px', color: '#94a3b8', fontWeight: 500 }}>Instance ID</th>
                    <th style={{ padding: '12px 16px', color: '#94a3b8', fontWeight: 500 }}>Bot Code</th>
                    <th style={{ padding: '12px 16px', color: '#94a3b8', fontWeight: 500 }}>Mode</th>
                    <th style={{ padding: '12px 16px', color: '#94a3b8', fontWeight: 500 }}>Risk Ceiling</th>
                    <th style={{ padding: '12px 16px', color: '#94a3b8', fontWeight: 500 }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {userInstances.map((inst, idx) => {
                    const template = templates.find(t => t.id === inst.botTemplateId)
                    return (
                      <tr key={inst.id} style={{ borderBottom: idx === userInstances.length - 1 ? 'none' : '1px solid #1f2b45' }}>
                        <td style={{ padding: '12px 16px', fontFamily: 'JetBrains Mono, monospace', fontSize: '12px', color: '#64748b' }}>
                          {inst.id.substring(0, 12)}...
                        </td>
                        <td style={{ padding: '12px 16px', fontWeight: 500 }}>{template?.code || 'Unknown'}</td>
                        <td style={{ padding: '12px 16px' }}>
                          <span style={{ backgroundColor: '#172033', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>
                            {(inst.mode || 'paper').toUpperCase()}
                          </span>
                        </td>
                        <td style={{ padding: '12px 16px' }}>{inst.riskCeilingPct}%</td>
                        <td style={{ padding: '12px 16px' }}>
                          <span style={{ color: inst.status === 'active' ? '#34d399' : '#f87171', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: inst.status === 'active' ? '#34d399' : '#f87171', display: 'inline-block' }}></span>
                            {(inst.status || 'unknown').toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
