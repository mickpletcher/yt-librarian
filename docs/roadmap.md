# Roadmap

## Implemented in the initial release

- Persistent-profile Liked Videos collection with safety guards and throttling.
- Saved playlist discovery, per-playlist inventory, membership history, and advisory optimization.
- Normalized SQLite schema and Alembic migration.
- Incremental fingerprint-based synchronization.
- Deterministic multi-category rules and optional OpenAI classification.
- Review queue, text search, category management, durable playlist plans, and Streamlit UI.
- Mocked tests, static analysis, structured logs, and cross-platform scripts.

## Next

- Reconcile the 19 count mismatches from the completed 85-playlist read-only crawl, diagnose intermittent four-card discovery, and prove a repeatable full local import behind the expected-count guard.
- Validate one pending action with `apply-plan --validate`, then complete one explicitly approved add-only action against a disposable playlist and rerun it to prove idempotency.
- Validate and version selectors against multiple YouTube layouts and languages.
- Add privacy-safe selector diagnostics and sanitized structural fixtures for future YouTube layout changes.
- Add deterministic rule-set versions and controlled reclassification previews.
- Add explicit retention policies and sanitized field-level exports after the current counts-only inventory.
- Add local embedding providers, vector storage, and semantic search behind the existing interface.
- Add richer rule-learning suggestions and review analytics.
- Package a signed Windows desktop launcher after the browser workflow stabilizes.

Semantic search is intentionally represented by an interface and explicit unavailable result. It will not silently send transcript data to a remote embedding provider.
