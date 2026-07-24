-- Per-asset kill switches: the operator can halt entries for one asset
-- (e.g. ETH on a bad day) while the others keep trading. Missing row = enabled.
CREATE TABLE IF NOT EXISTS `asset_state` (
	`asset` text PRIMARY KEY NOT NULL,
	`enabled` integer NOT NULL DEFAULT 1,
	`updated_at` integer NOT NULL
);
