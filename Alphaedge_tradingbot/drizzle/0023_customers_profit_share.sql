-- Customers, per-customer profit share, wallet flows and the fee ledger.
-- Additive only: no existing table is touched.
CREATE TABLE IF NOT EXISTS `customers` (
  `id` text PRIMARY KEY NOT NULL,
  `user_id` text,
  `name` text NOT NULL,
  `email` text NOT NULL,
  `wallet_address` text NOT NULL,
  `venue` text DEFAULT 'hyperliquid' NOT NULL,
  `profit_share_pct` real NOT NULL,
  `status` text DEFAULT 'active' NOT NULL,
  `initial_capital` real NOT NULL,
  `sync_from` integer NOT NULL,
  `notes` text,
  `created_by` text NOT NULL,
  `created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `customers_wallet_address_unique` ON `customers` (`wallet_address`);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_customers_email` ON `customers` (`email`);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `customer_rate_changes` (
  `id` text PRIMARY KEY NOT NULL,
  `customer_id` text NOT NULL,
  `pct` real NOT NULL,
  `effective_at` integer NOT NULL,
  `set_by` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_rate_changes_customer` ON `customer_rate_changes` (`customer_id`, `effective_at`);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `customer_state` (
  `customer_id` text PRIMARY KEY NOT NULL,
  `capital_basis` real NOT NULL,
  `outstanding_fee` real DEFAULT 0 NOT NULL,
  `last_balance` real,
  `last_synced_at` integer,
  `last_ledger_time` integer,
  `last_error` text,
  `sync_lock_until` integer
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `wallet_flows` (
  `id` text PRIMARY KEY NOT NULL,
  `customer_id` text NOT NULL,
  `kind` text NOT NULL,
  `amount` real NOT NULL,
  `venue_fee` real DEFAULT 0 NOT NULL,
  `counterparty` text,
  `tx_hash` text,
  `occurred_at` integer NOT NULL,
  `raw_json` text NOT NULL,
  `processed_at` integer
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_wallet_flows_customer_time` ON `wallet_flows` (`customer_id`, `occurred_at`);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `fee_events` (
  `id` text PRIMARY KEY NOT NULL,
  `customer_id` text NOT NULL,
  `flow_id` text,
  `kind` text NOT NULL,
  `balance_before` real,
  `capital_before` real NOT NULL,
  `outstanding_before` real NOT NULL,
  `profit` real,
  `pct` real,
  `fee` real DEFAULT 0 NOT NULL,
  `amount` real DEFAULT 0 NOT NULL,
  `capital_after` real NOT NULL,
  `outstanding_after` real NOT NULL,
  `estimated` integer DEFAULT 0 NOT NULL,
  `note` text,
  `created_by` text NOT NULL,
  `created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `idx_fee_events_customer_time` ON `fee_events` (`customer_id`, `created_at`);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `idx_fee_events_flow_kind` ON `fee_events` (`flow_id`, `kind`);
