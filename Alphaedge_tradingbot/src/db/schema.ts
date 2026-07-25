import { sqliteTable, text, integer, real, primaryKey } from 'drizzle-orm/sqlite-core';
import type { AdapterAccountType } from 'next-auth/adapters';

export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  name: text('name'),
  email: text('email').notNull().unique(),
  emailVerified: integer('emailVerified', { mode: 'timestamp_ms' }),
  image: text('image'),
  kycStatus: text('kyc_status').default('pending'), // 'pending' | 'verified'
  role: text('role').notNull().default('pending'), // 'owner' | 'viewer' | 'pending' | 'blocked'
  createdAt: integer('created_at').notNull().$defaultFn(() => Date.now())
});

export const accounts = sqliteTable(
  "account",
  {
    userId: text("userId")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    type: text("type").$type<AdapterAccountType>().notNull(),
    provider: text("provider").notNull(),
    providerAccountId: text("providerAccountId").notNull(),
    refresh_token: text("refresh_token"),
    access_token: text("access_token"),
    expires_at: integer("expires_at"),
    token_type: text("token_type"),
    scope: text("scope"),
    id_token: text("id_token"),
    session_state: text("session_state"),
  },
  (account) => ({
    compoundKey: primaryKey({
      columns: [account.provider, account.providerAccountId],
    }),
  })
);

export const sessions = sqliteTable("session", {
  sessionToken: text("sessionToken").primaryKey(),
  userId: text("userId")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  expires: integer("expires", { mode: "timestamp_ms" }).notNull(),
});

export const verificationTokens = sqliteTable(
  "verificationToken",
  {
    identifier: text("identifier").notNull(),
    token: text("token").notNull(),
    expires: integer("expires", { mode: "timestamp_ms" }).notNull(),
  },
  (vt) => ({
    compoundKey: primaryKey({ columns: [vt.identifier, vt.token] }),
  })
);

export const authenticators = sqliteTable(
  "authenticator",
  {
    credentialID: text("credentialID").notNull().unique(),
    userId: text("userId")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    providerAccountId: text("providerAccountId").notNull(),
    credentialPublicKey: text("credentialPublicKey").notNull(),
    counter: integer("counter").notNull(),
    credentialDeviceType: text("credentialDeviceType").notNull(),
    credentialBackedUp: integer("credentialBackedUp", {
      mode: "boolean",
    }).notNull(),
    transports: text("transports"),
  },
  (authenticator) => ({
    compoundKey: primaryKey({
      columns: [authenticator.userId, authenticator.credentialID],
    }),
  })
);

export const exchangeConnections = sqliteTable('exchange_connections', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => users.id).notNull(),
  exchange: text('exchange').notNull(), // 'hyperliquid'
  encryptedApiKey: text('encrypted_api_key').notNull(),
  encryptionIv: text('encryption_iv').notNull(),
  encryptionTag: text('encryption_tag').notNull(),
  status: text('status').default('active'), // 'active' | 'revoked'
  lastVerifiedAt: integer('last_verified_at').notNull()
});

export const botTemplates = sqliteTable('bot_templates', {
  id: text('id').primaryKey(),
  code: text('code').notNull(), // e.g. HL-BREAKOUT-BTC, HL-BREAKOUT-ETH
  assetClass: text('asset_class').notNull(), // 'BTC' | 'ETH' | 'XAUUSD'
  status: text('status').default('in_assay'), // 'in_assay' | 'live'
  minWinRate: real('min_win_rate'),
  minExpectancy: real('min_expectancy')
});

export const botInstances = sqliteTable('bot_instances', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => users.id).notNull(),
  botTemplateId: text('bot_template_id').references(() => botTemplates.id).notNull(),
  exchangeConnectionId: text('exchange_connection_id').references(() => exchangeConnections.id).notNull(),
  mode: text('mode').default('paper'), // 'paper' | 'live'
  riskCeilingPct: real('risk_ceiling_pct').notNull(),
  maxNotional: real('max_notional').notNull(),
  status: text('status').default('active') // 'active' | 'paused' | 'kill_switched'
});

export const signals = sqliteTable('signals', {
  id: text('id').primaryKey(),
  botTemplateId: text('bot_template_id').references(() => botTemplates.id).notNull(),
  assetClass: text('asset_class').notNull(),
  direction: text('direction').notNull(), // 'LONG' | 'SHORT' | 'EXIT'
  entryPrice: real('entry_price'),
  sl: real('sl'),
  tp: real('tp'),
  timestamp: integer('timestamp').notNull()
});

export const orders = sqliteTable('orders', {
  id: text('id').primaryKey(),
  botInstanceId: text('bot_instance_id').references(() => botInstances.id).notNull(),
  signalId: text('signal_id').references(() => signals.id),
  exchangeOrderId: text('exchange_order_id'),
  side: text('side').notNull(), // 'buy' | 'sell'
  qty: real('qty').notNull(),
  price: real('price').notNull(),
  status: text('status').notNull(), // 'submitted' | 'filled' | 'cancelled' | 'rejected'
  submittedAt: integer('submitted_at').notNull(),
  filledAt: integer('filled_at')
});

export const ledgerEntries = sqliteTable('ledger_entries', {
  id: text('id').primaryKey(),
  prevHash: text('prev_hash').notNull(),
  hash: text('hash').notNull(),
  entityType: text('entity_type').notNull(), // 'signal' | 'fill' | 'risk_event'
  entityId: text('entity_id').notNull(),
  payloadJson: text('payload_json').notNull(),
  timestamp: integer('timestamp').notNull()
});

export const riskEvents = sqliteTable('risk_events', {
  id: text('id').primaryKey(),
  botInstanceId: text('bot_instance_id').references(() => botInstances.id).notNull(),
  type: text('type').notNull(), // 'ceiling_breach' | 'drawdown_halt' | 'kill_switch'
  detail: text('detail').notNull(),
  timestamp: integer('timestamp').notNull()
});

export const earlyAccessLeads = sqliteTable('early_access_leads', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  role: text('role').notNull().default('capital-builder'),
  capitalBand: text('capital_band').notNull().default('exploring'),
  marketFocus: text('market_focus').notNull().default('multi-asset'),
  createdAt: integer('created_at').notNull()
});

// Shared demo account: single row. Equity = baseUsd + PnL of rounds settled
// at/after startedAt. Resetting the demo = bumping startedAt (non-destructive).
export const demoAccount = sqliteTable('demo_account', {
  id: text('id').primaryKey(), // always 'demo'
  baseUsd: real('base_usd').notNull(),
  startedAt: integer('started_at').notNull(),
  // Operator override: daily counters + circuit breakers count from here when
  // later than the last 13:00 UTC roll. Null = normal daily rhythm.
  dayResetAt: integer('day_reset_at'),
});

// Canonical server-side engine rounds: deterministic 90s epochs per asset.
// The server locks strikes, takes positions, and settles — viewers only read.
export const engineRounds = sqliteTable('engine_rounds', {
  id: text('id').primaryKey(), // `${asset}_${epoch}`
  asset: text('asset').notNull(),
  epoch: integer('epoch').notNull(), // floor(startMs / 90_000)
  startedAt: integer('started_at').notNull(),
  expiresAt: integer('expires_at').notNull(),
  strikePrice: real('strike_price').notNull(),
  status: text('status').notNull().default('open'), // 'open' | 'settled' | 'skipped'
  side: text('side'), // 'BUY' | 'SELL' | null while flat
  size: integer('size'),
  entryPrice: real('entry_price'),
  entryAt: integer('entry_at'),
  entryPYes: real('entry_p_yes'),
  levelSizes: text('level_sizes'), // JSON: {"1": contracts, "2": ..., "3": ...}
  skipReason: text('skip_reason'), // e.g. 'regime:FOMC rate decision' when gated
  settledAt: integer('settled_at'),
});

// ---------------------------------------------------------------------------
// Regime Guard — risk-off gating for high-impact events (FOMC, hacks, shocks).
//
// regime_state: single row (id='regime') carrying the manual override and the
// auto shock-detector cooldown. regime_events: pre-scheduled blackout windows
// (buffers already applied to start/end). regime_log: every mode transition,
// for audit and for showing users the engine sat out on purpose.
export const regimeState = sqliteTable('regime_state', {
  id: text('id').primaryKey(), // always 'regime'
  manualMode: text('manual_mode'), // 'caution' | 'lockdown' | null = no override
  manualReason: text('manual_reason'),
  manualUntil: integer('manual_until'), // optional TTL (ms); null = until released
  shockUntil: integer('shock_until'), // auto-lockdown release time (ms)
  shockReason: text('shock_reason'),
  lastMode: text('last_mode').notNull().default('normal'), // for transition logging
  calendarSyncedAt: integer('calendar_synced_at'), // last economic-calendar feed sync attempt
  updatedAt: integer('updated_at').notNull(),
});

export const regimeEvents = sqliteTable('regime_events', {
  id: text('id').primaryKey(),
  label: text('label').notNull(), // e.g. 'FOMC rate decision'
  kind: text('kind').notNull(), // 'fed' | 'cpi' | 'nfp' | 'crypto' | 'other'
  severity: text('severity').notNull().default('lockdown'), // 'caution' | 'lockdown'
  startAt: integer('start_at').notNull(), // blackout window start (ms, buffers included)
  endAt: integer('end_at').notNull(),
  createdAt: integer('created_at').notNull(),
});

export const regimeLog = sqliteTable('regime_log', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  mode: text('mode').notNull(), // 'normal' | 'caution' | 'lockdown'
  reason: text('reason').notNull(),
  source: text('source').notNull(), // 'manual' | 'auto' | 'calendar' | 'system'
  at: integer('at').notNull(),
});

// Onboarding answers from newly signed-in (pending) users. Keyed by the
// session email so answers always match the Google account being approved.
export const onboardingProfiles = sqliteTable('onboarding_profiles', {
  email: text('email').primaryKey(),
  fullName: text('full_name').notNull(),
  levelInterest: text('level_interest').notNull(), // 'demo' | 'level-1' | 'level-2' | 'level-3' | 'undecided'
  capitalBand: text('capital_band').notNull(),
  experience: text('experience').notNull(),
  note: text('note'),
  createdAt: integer('created_at').notNull(),
  updatedAt: integer('updated_at').notNull(),
});

// Rolling loss-breaker state per tier. The -15% stop releases 24h after the
// trip (not on a calendar boundary), so the trip time must persist.
export const levelLocks = sqliteTable('level_locks', {
  level: integer('level').primaryKey(),
  lossLockedAt: integer('loss_locked_at'), // ms of the -15% trip; null = clear
  releasedAt: integer('released_at'),      // ms the lock expired
  releaseEquity: real('release_equity'),   // equity at release — re-baselines the threshold
  profitLockedAt: integer('profit_locked_at'), // ms the +28% ceiling was booked; sticky for the UTC day
  updatedAt: integer('updated_at').notNull(),
});

// Per-asset kill switches (owner-operated). Missing row = enabled.
export const assetState = sqliteTable('asset_state', {
  asset: text('asset').primaryKey(),
  enabled: integer('enabled').notNull().default(1),
  updatedAt: integer('updated_at').notNull(),
});

export const simulatorTrades = sqliteTable('simulator_trades', {
  id: text('id').primaryKey(),
  level: integer('level').notNull().default(0), // 1|2|3 subscription levels; 0 = legacy
  roundId: integer('round_id').notNull(),
  asset: text('asset').notNull(),
  timestamp: text('timestamp').notNull(),
  strikePrice: real('strike_price').notNull(),
  expiryPrice: real('expiry_price').notNull(),
  side: text('side').notNull(),
  size: integer('size').notNull(),
  entryPrice: real('entry_price').notNull(),
  exitPrice: real('exit_price').notNull(),
  outcome: text('outcome').notNull(),
  pnl: real('pnl').notNull(),
  createdAt: integer('created_at').notNull()
});

