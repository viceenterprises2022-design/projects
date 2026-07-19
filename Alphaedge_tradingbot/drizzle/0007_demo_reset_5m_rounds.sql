-- One-time demo reset for the switch to 5-minute rounds:
-- equity returns to the clean $10,000 base at deploy time, and any
-- in-flight 90s rounds are voided so they can't settle into the fresh
-- ledger. Historical rows are preserved (owner-only archive view).
UPDATE demo_account SET started_at = CAST(strftime('%s','now') AS INTEGER) * 1000, base_usd = 10000 WHERE id = 'demo';
--> statement-breakpoint
UPDATE engine_rounds SET status = 'skipped', settled_at = CAST(strftime('%s','now') AS INTEGER) * 1000 WHERE status = 'open';
