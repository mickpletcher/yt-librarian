# Database schema

The initial Alembic migration creates:

- `videos`: normalized current metadata and processing statuses, keyed by unique YouTube ID.
- `transcripts`: per-video, per-language transcript text, segments, hashes, and retrieval outcomes.
- `categories`: hierarchical local categories and optional YouTube playlist mappings.
- `video_categories`: many-to-many assignments with source, confidence, explanation, approval, and primary status.
- `classification_runs`: auditable AI requests and outcomes.
- `classification_rules`: persisted rule metadata and match configuration.
- `sync_runs`: synchronization checkpoints, counters, status, and errors.
- `browser_actions`: stable, idempotent playlist action records with attempt history.

Timestamps are stored in UTC. Flexible provider and YouTube payloads use JSON columns, which SQLAlchemy maps to SQLite JSON storage. SQLite foreign keys are enabled on every connection.

Run `uv run alembic upgrade head`. Back up the local database before applying later schema changes.
