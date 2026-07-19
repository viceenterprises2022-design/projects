CREATE TABLE `regime_events` (
	`id` text PRIMARY KEY NOT NULL,
	`label` text NOT NULL,
	`kind` text NOT NULL,
	`severity` text DEFAULT 'lockdown' NOT NULL,
	`start_at` integer NOT NULL,
	`end_at` integer NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `regime_log` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`mode` text NOT NULL,
	`reason` text NOT NULL,
	`source` text NOT NULL,
	`at` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `regime_state` (
	`id` text PRIMARY KEY NOT NULL,
	`manual_mode` text,
	`manual_reason` text,
	`manual_until` integer,
	`shock_until` integer,
	`shock_reason` text,
	`last_mode` text DEFAULT 'normal' NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
ALTER TABLE `engine_rounds` ADD `skip_reason` text;--> statement-breakpoint
-- Seed the near-term macro blackout calendar (windows in UTC ms, buffers
-- applied: FOMC decision 18:00 UTC + presser; CPI/NFP prints 12:30 UTC).
-- Dates verified against the Fed and BLS 2026 release schedules.
INSERT OR IGNORE INTO `regime_events` (`id`, `label`, `kind`, `severity`, `start_at`, `end_at`, `created_at`) VALUES
('ev_fomc_2026_07_29', 'FOMC rate decision', 'fed', 'lockdown', 1785344400000, 1785357000000, 1784477624000),
('ev_nfp_2026_08_07', 'US nonfarm payrolls', 'nfp', 'lockdown', 1786104000000, 1786109400000, 1784477624000),
('ev_cpi_2026_08_12', 'US CPI release (July print)', 'cpi', 'lockdown', 1786536000000, 1786541400000, 1784477624000),
('ev_fomc_2026_09_16', 'FOMC rate decision', 'fed', 'lockdown', 1789578000000, 1789590600000, 1784477624000);
