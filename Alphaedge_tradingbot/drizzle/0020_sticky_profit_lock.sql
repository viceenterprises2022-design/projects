-- Sticky profit lock: once a tier books its daily ceiling it stays locked for
-- the rest of the UTC day, even if already-open positions settle at a loss and
-- drag it back under the threshold. Stamped with the trip time; a value older
-- than the current day window is treated as clear.
ALTER TABLE `level_locks` ADD COLUMN `profit_locked_at` integer;
