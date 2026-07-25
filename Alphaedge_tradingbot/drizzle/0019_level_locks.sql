-- Rolling loss-breaker state. The -15% stop no longer releases on a calendar
-- boundary: a tripped tier reopens LOSS_LOCK_HOURS (default 24h) after the
-- trip, so the trip time must persist across serverless instances.
-- release_equity re-baselines the threshold on release, so a second trip costs
-- 15% of the reduced equity instead of re-firing on the day's earlier losses.
-- Missing row = tier not locked.
CREATE TABLE IF NOT EXISTS `level_locks` (
	`level` integer PRIMARY KEY NOT NULL,
	`loss_locked_at` integer,
	`released_at` integer,
	`release_equity` real,
	`updated_at` integer NOT NULL
);
