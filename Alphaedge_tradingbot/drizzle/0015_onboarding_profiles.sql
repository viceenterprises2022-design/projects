-- Onboarding answers collected from pending users after Google sign-in,
-- keyed by session email so they line up with Access Control approvals.
CREATE TABLE IF NOT EXISTS `onboarding_profiles` (
	`email` text PRIMARY KEY NOT NULL,
	`full_name` text NOT NULL,
	`level_interest` text NOT NULL,
	`capital_band` text NOT NULL,
	`experience` text NOT NULL,
	`note` text,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
