ALTER TABLE `engine_rounds` ADD `level_sizes` text;--> statement-breakpoint
ALTER TABLE `simulator_trades` ADD `level` integer DEFAULT 0 NOT NULL;--> statement-breakpoint
-- Levels comparison must start from a common origin: restart the demo window
-- so Level 1/2/3 ledgers begin together at their clean bases.
UPDATE demo_account SET started_at = CAST(strftime('%s','now') AS INTEGER) * 1000, base_usd = 10000 WHERE id = 'demo';
--> statement-breakpoint
UPDATE engine_rounds SET status = 'skipped', settled_at = CAST(strftime('%s','now') AS INTEGER) * 1000 WHERE status = 'open';
