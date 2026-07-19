-- Level economics changed (L1 $5K/30, L2 $10K/45, L3 $25K+/60): restart the
-- demo window so all levels begin together under the new bases, and void any
-- in-flight rounds from the old configuration.
UPDATE demo_account SET started_at = CAST(strftime('%s','now') AS INTEGER) * 1000 WHERE id = 'demo';
--> statement-breakpoint
UPDATE engine_rounds SET status = 'skipped', settled_at = CAST(strftime('%s','now') AS INTEGER) * 1000 WHERE status = 'open';
