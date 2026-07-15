import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull(),
  kycStatus: text('kyc_status').default('pending'), // 'pending' | 'verified'
  createdAt: integer('created_at').notNull()
});

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

export const simulatorTrades = sqliteTable('simulator_trades', {
  id: text('id').primaryKey(),
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

