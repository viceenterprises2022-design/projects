-- Owner-requested restart: zero all tier ledgers and daily counters so
-- trading begins fresh under the final configuration ($250 flat sizing,
-- Demo $10K/45, L1 $5K/30, L2 $10K/45, L3 $25K+/60).
UPDATE demo_account SET started_at = CAST(strftime('%s','now') AS INTEGER) * 1000 WHERE id = 'demo';
--> statement-breakpoint
UPDATE engine_rounds SET status = 'skipped', settled_at = CAST(strftime('%s','now') AS INTEGER) * 1000 WHERE status = 'open';
