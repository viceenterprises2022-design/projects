CREATE TABLE `early_access_leads` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`email` text NOT NULL,
	`role` text DEFAULT 'capital-builder' NOT NULL,
	`capital_band` text DEFAULT 'exploring' NOT NULL,
	`market_focus` text DEFAULT 'multi-asset' NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `early_access_leads_email_unique` ON `early_access_leads` (`email`);