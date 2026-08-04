# Roadmap

## Implemented in the initial release

- Persistent-profile Liked Videos collection with safety guards and throttling.
- Normalized SQLite schema and Alembic migration.
- Incremental fingerprint-based synchronization.
- Deterministic multi-category rules and optional OpenAI classification.
- Review queue, text search, category management, durable playlist plans, and Streamlit UI.
- Mocked tests, static analysis, structured logs, and cross-platform scripts.

## Next

- Validate and version selectors against multiple YouTube layouts and languages.
- Add resumable metadata enrichment and transcript extraction coverage.
- Add local embedding providers, vector storage, and semantic search behind the existing interface.
- Add export and encrypted backup workflows that exclude browser authentication state.
- Add richer rule-learning suggestions and review analytics.
- Package a signed Windows desktop launcher after the browser workflow stabilizes.

Semantic search is intentionally represented by an interface and explicit unavailable result. It will not silently send transcript data to a remote embedding provider.
