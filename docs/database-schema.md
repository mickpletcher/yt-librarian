# Database schema

The Alembic migrations create:

- `videos`: normalized current metadata and processing statuses, keyed by unique YouTube ID.
- `transcripts`: per-video, per-language transcript text, segments, hashes, retrieval outcomes, attempt counts, and retry eligibility.
- `categories`: hierarchical local categories and optional YouTube playlist mappings.
- `video_categories`: many-to-many assignments with source, confidence, explanation, approval, and primary status.
- `classification_runs`: auditable AI requests and outcomes.
- `classification_rules`: persisted rule metadata and match configuration.
- `sync_runs`: operation-specific synchronization checkpoints, counters, status, and errors.
- `browser_actions`: stable, idempotent playlist action records with attempt history.
- `youtube_playlists`: saved playlist identity, current name, canonical URL, system type, reported count, timestamps, and raw metadata.
- `playlist_memberships`: active and historical video membership for each saved playlist, including observed position and timestamps.

`youtube_playlists.youtube_playlist_id` is unique. `playlist_memberships` has one row per playlist and video pair. A missing membership is marked inactive after a successful crawl instead of being deleted. Liked Videos and Watch Later are identified as system playlists so optimization can exclude them from regular-playlist duplicate and categorization calculations.

Timestamps are stored in UTC. Flexible provider and YouTube payloads use JSON columns, which SQLAlchemy maps to SQLite JSON storage. SQLite foreign keys are enabled on every connection.

Use `uv run ykm init-db` for normal migrations. It takes the application lock and creates a verified pre-migration backup when an existing database is behind the current migration head. Use `ykm db-check`, `ykm db-backup`, and the explicit `ykm db-restore <path> --apply` workflow for integrity and recovery.
