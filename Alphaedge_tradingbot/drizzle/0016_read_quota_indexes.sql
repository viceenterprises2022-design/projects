-- Turso bills rows scanned as row reads. The engine tick aggregates
-- per-level stats over the demo window on every poll; without indexes each
-- poll scans the whole simulator_trades table (archive rows included).
-- These indexes confine each scan to the rows that actually match.
CREATE INDEX IF NOT EXISTS idx_sim_trades_level_created ON simulator_trades (level, created_at);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS idx_sim_trades_asset_round ON simulator_trades (asset, round_id);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS idx_engine_rounds_status_expires ON engine_rounds (status, expires_at);
