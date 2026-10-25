-- Analytics streams the full demo window ordered by (created_at, id) using
-- keyset pagination. The existing (level, created_at) index cannot serve an
-- all-tiers range on created_at, so without this every analytics REFRESH
-- scans the whole table, archive rows included, and Turso bills each one.
CREATE INDEX IF NOT EXISTS idx_sim_trades_created_id ON simulator_trades (created_at, id);
