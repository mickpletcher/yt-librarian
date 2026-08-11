# Architecture

YouTube Knowledge Manager is a local-first layered application.

1. Browser adapters discover the saved playlist library, read individual playlists, and perform explicitly approved playlist additions.
2. Collection services normalize browser results and persist videos and playlist memberships immediately.
3. Repositories own SQLAlchemy queries and idempotent writes.
4. Classification combines deterministic rules with an optional AI provider.
5. Review services expose uncertain or conflicting assignments for human approval.
6. Planning turns approved assignments into durable browser actions.
7. The executor applies pending actions, records outcomes, and safely resumes failures.
8. The CLI and Streamlit UI call services. They never query tables directly.

SQLite is the system of record. Each sync records its operation, counters, status, and terminal error. Each browser write has a stable action key, so rerunning an interrupted operation does not duplicate work. A startup recovery step moves abandoned running actions to failed before retry. Video fingerprints prevent unchanged items from being reclassified.

Saved playlist synchronization uses YouTube playlist IDs as stable identity. Only a complete playlist crawl whose collected count reconciles with the displayed available count may mark previously active memberships inactive. Failed, interrupted, limited, or count-mismatched crawls preserve existing membership state. An unrestricted write also requires an operator-supplied expected library discovery count and stops before playlist processing if YouTube returns a partial library view. Optimization reads this local inventory and produces metrics plus add-only proposals. It never performs destructive YouTube actions.

The Playwright layer is asynchronous. Persistence and UI layers are synchronous because SQLite and Streamlit are simplest in that model. The sync service bridges them at the command boundary.

The application deliberately does not expose password fields, accept exported cookies, or automate login. A dedicated persistent browser profile lets the user authenticate directly with Google.

All database and browser mutation workflows use a file-based single-writer lock adjacent to SQLite. Lock recovery is explicit. Abandoned synchronization and browser-action rows are recovered to failed state before retry. Database migrations, backup, restore, integrity checks, and counts-only data inventory live in services called by the CLI. Transcript enrichment stores durable attempt and retry state. AI providers have bounded retries, timeouts, daily token limits, and locally configured cost rates.
