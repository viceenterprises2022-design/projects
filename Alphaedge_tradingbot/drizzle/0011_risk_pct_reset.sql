-- Switch to 2% fixed-fractional sizing: restart all tier ledgers and daily
-- counters for a clean test under the new sizing model.
UPDATE demo_account SET started_at = CAST(strftime('%s','now') AS INTEGER) * 1000 WHERE id = 'demo';
--> statement-breakpoint
UPDATE engine_rounds SET status = 'skipped', settled_at = CAST(strftime('%s','now') AS INTEGER) * 1000 WHERE status = 'open';
