# Architecture

YouTube Knowledge Manager is a local-first layered application.

1. Browser adapters read YouTube and perform explicitly approved playlist additions.
2. Collection services normalize browser results and persist discoveries immediately.
3. Repositories own SQLAlchemy queries and idempotent writes.
4. Classification combines deterministic rules with an optional AI provider.
5. Review services expose uncertain or conflicting assignments for human approval.
6. Planning turns approved assignments into durable browser actions.
7. The executor applies pending actions, records outcomes, and safely resumes failures.
8. The CLI and Streamlit UI call services. They never query tables directly.

SQLite is the system of record. Each sync records counters and status. Each browser write has a stable action key, so rerunning an interrupted operation does not duplicate work. Video fingerprints prevent unchanged items from being reclassified.

The Playwright layer is asynchronous. Persistence and UI layers are synchronous because SQLite and Streamlit are simplest in that model. The sync service bridges them at the command boundary.

The application deliberately does not expose password fields, accept exported cookies, or automate login. A dedicated persistent browser profile lets the user authenticate directly with Google.
