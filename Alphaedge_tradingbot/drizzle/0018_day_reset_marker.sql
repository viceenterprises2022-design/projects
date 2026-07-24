-- Operator day-reset marker: bumping day_reset_at restarts the daily quota
-- counters and the daily loss circuit breaker window immediately, WITHOUT
-- touching ledger history or cumulative demo-window stats.
ALTER TABLE `demo_account` ADD COLUMN `day_reset_at` integer;
