CREATE TABLE `engine_rounds` (
	`id` text PRIMARY KEY NOT NULL,
	`asset` text NOT NULL,
	`epoch` integer NOT NULL,
	`started_at` integer NOT NULL,
	`expires_at` integer NOT NULL,
	`strike_price` real NOT NULL,
	`status` text DEFAULT 'open' NOT NULL,
	`side` text,
	`size` integer,
	`entry_price` real,
	`entry_at` integer,
	`entry_p_yes` real,
	`settled_at` integer
);
