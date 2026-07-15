CREATE TABLE `simulator_trades` (
	`id` text PRIMARY KEY NOT NULL,
	`round_id` integer NOT NULL,
	`asset` text NOT NULL,
	`timestamp` text NOT NULL,
	`strike_price` real NOT NULL,
	`expiry_price` real NOT NULL,
	`side` text NOT NULL,
	`size` integer NOT NULL,
	`entry_price` real NOT NULL,
	`exit_price` real NOT NULL,
	`outcome` text NOT NULL,
	`pnl` real NOT NULL,
	`created_at` integer NOT NULL
);
