-- Changelog publication gate. Entry CONTENT lives in version control (so an
-- entry ships in the same commit as the change it describes and cannot drift);
-- only the decision to publish lives here. A row means published — no row means
-- the entry is a draft and viewers never see it.
CREATE TABLE IF NOT EXISTS `changelog_publications` (
	`entry_id` text PRIMARY KEY NOT NULL,
	`published_at` integer NOT NULL,
	`published_by` text
);
