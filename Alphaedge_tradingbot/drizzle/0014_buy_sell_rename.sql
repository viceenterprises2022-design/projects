-- Rename position sides to industry-standard BUY/SELL across all stored rows
-- (including the owner-only archive) so DB values match the renamed engine.
UPDATE simulator_trades SET side = 'BUY' WHERE side = 'YES';
--> statement-breakpoint
UPDATE simulator_trades SET side = 'SELL' WHERE side = 'NO';
--> statement-breakpoint
UPDATE engine_rounds SET side = 'BUY' WHERE side = 'YES';
--> statement-breakpoint
UPDATE engine_rounds SET side = 'SELL' WHERE side = 'NO';
