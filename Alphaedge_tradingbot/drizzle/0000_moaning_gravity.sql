CREATE TABLE `bot_instances` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`bot_template_id` text NOT NULL,
	`exchange_connection_id` text NOT NULL,
	`mode` text DEFAULT 'paper',
	`risk_ceiling_pct` real NOT NULL,
	`max_notional` real NOT NULL,
	`status` text DEFAULT 'active',
	FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`bot_template_id`) REFERENCES `bot_templates`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`exchange_connection_id`) REFERENCES `exchange_connections`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `bot_templates` (
	`id` text PRIMARY KEY NOT NULL,
	`code` text NOT NULL,
	`asset_class` text NOT NULL,
	`status` text DEFAULT 'in_assay',
	`min_win_rate` real,
	`min_expectancy` real
);
--> statement-breakpoint
CREATE TABLE `exchange_connections` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`exchange` text NOT NULL,
	`encrypted_api_key` text NOT NULL,
	`encryption_iv` text NOT NULL,
	`encryption_tag` text NOT NULL,
	`status` text DEFAULT 'active',
	`last_verified_at` integer NOT NULL,
	FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `ledger_entries` (
	`id` text PRIMARY KEY NOT NULL,
	`prev_hash` text NOT NULL,
	`hash` text NOT NULL,
	`entity_type` text NOT NULL,
	`entity_id` text NOT NULL,
	`payload_json` text NOT NULL,
	`timestamp` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `orders` (
	`id` text PRIMARY KEY NOT NULL,
	`bot_instance_id` text NOT NULL,
	`signal_id` text,
	`exchange_order_id` text,
	`side` text NOT NULL,
	`qty` real NOT NULL,
	`price` real NOT NULL,
	`status` text NOT NULL,
	`submitted_at` integer NOT NULL,
	`filled_at` integer,
	FOREIGN KEY (`bot_instance_id`) REFERENCES `bot_instances`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`signal_id`) REFERENCES `signals`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `risk_events` (
	`id` text PRIMARY KEY NOT NULL,
	`bot_instance_id` text NOT NULL,
	`type` text NOT NULL,
	`detail` text NOT NULL,
	`timestamp` integer NOT NULL,
	FOREIGN KEY (`bot_instance_id`) REFERENCES `bot_instances`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `signals` (
	`id` text PRIMARY KEY NOT NULL,
	`bot_template_id` text NOT NULL,
	`asset_class` text NOT NULL,
	`direction` text NOT NULL,
	`entry_price` real,
	`sl` real,
	`tp` real,
	`timestamp` integer NOT NULL,
	FOREIGN KEY (`bot_template_id`) REFERENCES `bot_templates`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `users` (
	`id` text PRIMARY KEY NOT NULL,
	`email` text NOT NULL,
	`kyc_status` text DEFAULT 'pending',
	`created_at` integer NOT NULL
);
