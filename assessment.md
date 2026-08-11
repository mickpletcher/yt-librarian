# Project assessment

## Assessment metadata

| Item | Current value |
| --- | --- |
| Project | YouTube Knowledge Manager |
| Package | `youtube_knowledge_manager` |
| Version | 0.1.0 |
| Assessment date | 2026-08-11 |
| Lifecycle | Production candidate |
| Primary platform | Windows 11 |
| Supported runtime | Python 3.12 or newer |
| System of record | Local SQLite database |
| Live YouTube validation | Current read-only Liked Videos and complete saved-library crawls ran; playlist mismatches, intermittent partial discovery, repeatable full local import, and one controlled add-only action remain |
| Overall readiness | 4/5 production candidate. Code and local operations are hardened; account-specific live gates prevent an honest 5/5. |

Read this file before changing the project. Update it in the same change set whenever implementation, tests, documentation, risks, readiness, or priorities change.

## Executive assessment

The project has a coherent production-candidate architecture. Persistence, browser safety, Liked Videos and saved-playlist synchronization, deterministic and optional AI classification, human review, enrichment, advisory optimization, playlist planning and validation, search, recovery operations, CLI, Streamlit, migrations, structured logging, scripts, tests, and documentation are implemented.

The strongest design decision remains the separation between reads, local persistence, planning, validation, and browser writes. YouTube changes require explicit `--apply`. Target resolution prefers playlist ID and fails closed on mismatches or ambiguous names. Every addition has a stable action key, inventory recheck, durable attempt state, and interrupted-action recovery. Deletion, removal, move, merge, rename, and automatic playlist creation remain absent.

The product now discovers every saved playlist shown by YouTube and can inventory each playlist through a reusable collector. Stable playlist IDs, current names, reported counts, video positions, active memberships, and observation history are stored locally. Optimization reports duplicate regular-playlist placement, empty and oversized playlists, uncategorized saved videos, and missing approved category additions. It only creates local add-only plans. It does not automate removals, moves, merges, renames, creation, or deletion.

The largest remaining gap is account-specific reconciliation. A current read-only Liked Videos crawl collected 3,053 visible entries against a 3,142-video header that reported unavailable videos hidden. A complete saved-library read-only run discovered 85 playlists, observed 4,644 memberships and 3,497 unique videos, and isolated 19 playlist count mismatches. YouTube also intermittently returned only four playlist cards with no continuation. An exact expected-count guard now prevents that partial result from entering a full write, and a live write rehearsal proved it stopped before playlist processing. A repeatable full local import and one explicitly approved disposable-playlist add remain incomplete. Localization, experiments, private playlists, transcript availability, and security prompts remain external risks.

The local quality baseline is production-grade for this single-user tool. Ruff, strict mypy, 72 non-live tests, a 75% coverage floor, Bandit, frozen dependency auditing, migration round trips, CLI tests, Streamlit smoke tests, and tracked-private-file checks pass. Mocked tests cover the critical browser and recovery branches. Live YouTube behavior still requires controlled operator validation because it cannot be proven by CI.

Upgrade tracking now has a permanent tracked completion ledger and a local-only future backlog. The local backlog contains actionable ideas derived from this assessment. When an item ships, its stable ID and actual verification evidence move to `completed-upgrades.md`; it must not remain in both ledgers.

## Verified baseline

The following checks passed on Windows with Python 3.12.13:

| Check | Result |
| --- | --- |
| Dependency resolution | `uv sync --all-extras` completed and generated `uv.lock` |
| Ruff lint | Passed |
| Ruff format check | Passed |
| Strict mypy | Passed across 62 source files |
| Pytest | 72 passed, live YouTube tests excluded; 77.62% coverage against a 75% floor |
| Security lint | Bandit passed across `src` |
| Dependency audit | Frozen fully locked graph reports no known vulnerabilities |
| Alembic migrations | Upgrade and downgrade passed against a temporary SQLite database; `YKM_DATABASE_URL` targeting has regression coverage |
| Alembic schema drift | No new upgrade operations detected |
| CLI initialization | `ykm init-db` passed; safety tests assert rejected side effects consistently on Windows and Linux |
| CLI discovery | All expected commands appeared in `ykm --help` |
| Private runtime files | No database, browser profile, cookie, storage-state, transcript, or `.env` file was a Git candidate |
| Operator documentation | README verified against current CLI help, settings, scripts, safety boundaries, and Streamlit workflow |
| Upgrade tracking | `completed-upgrades.md` is tracked; root `future-upgrades.md` is local-only and ignored by Git |
| Dedicated profile authentication | Confirmed in normal Chrome; Liked Videos and account avatar visible |
| External browser attachment | Headless Chrome CDP smoke test passed on a private-data-free temporary profile |
| Live account crawl | Current authenticated read-only Liked Videos crawl collected 3,053 visible entries against a 3,142-video header that reported unavailable videos hidden; zero writes |
| Saved playlist discovery | One complete read-only run discovered 85 playlists; other sessions returned a partial four-card view, proving the expected-count write guard is necessary |
| Complete saved-library crawl | Read-only run observed 4,644 memberships and 3,497 unique videos; 19 playlists failed count reconciliation; zero writes |
| Full-write discovery guard | A live `--write --expect-playlists 85` rehearsal received four playlists and stopped before any playlist processing; database inventory stayed at two playlists and 21 memberships, then a verified pre-rehearsal backup restored the database to zero inventory rows |
| Database operations | Integrity, backup, restore, and migration backup tests passed on Windows |
| Single-writer protection | Active and stale lock behavior tested |
| Repeatable full saved-library import | Pending because current discovery is intermittent and 19 read-only playlist crawls require reconciliation |
| Live playlist write | Pending an explicitly selected disposable target |

Validation commands:

```powershell
uv sync --all-extras
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -m "not live_youtube" --cov=youtube_knowledge_manager --cov-report=term --cov-fail-under=75
uvx bandit -q -r src
uv run ykm init-db
uv run ykm --help
```

## Architecture assessment

### Boundaries

| Layer | Responsibility | Assessment |
| --- | --- | --- |
| `browser` | Persistent profile, safety detection, selectors, crawling, details, transcripts, playlist interaction | Strong fail-closed boundary with mocked coverage. Live DOM volatility remains external. |
| `collection` | Fingerprints, immediate video and membership persistence, enrichment, synchronization run tracking | Durable checkpoints, incomplete-crawl preservation, retry state, progress, and cancellation are present. |
| `db` | SQLAlchemy models, sessions, repositories, normalized video and playlist persistence | Strong single-user design with locking, integrity, backup, restore, and migrations. |
| `classification` | YAML schemas, deterministic rules, AI provider contract, provider adapters, result validation | Bounded provider calls, budget enforcement, cost recording, and failure isolation are present. Rule versioning remains future work. |
| `planning` | Durable, idempotent playlist proposals and controlled execution | Strong safety model with ID-aware resolution, dry validation, inventory recheck, and recovery. Live add remains a gate. |
| `search` | Text search, category filtering, local summaries, semantic-search boundary | Suitable alpha implementation. LIKE queries will eventually need FTS5. |
| `services` | Application workflows and advisory optimization consumed by CLI and UI | Correct boundary. Full-library query performance still needs current account evidence. |
| `ui` | Streamlit presentation and explicit user decisions | Collection progress and locked mutations are present. Bulk review remains future work. |
| `cli` | Operator workflow and explicit write controls | Clear dry-run boundaries, database preflight, recovery commands, and integration coverage. |

### Dependency direction

The UI calls services and repositories rather than embedding SQL. Planning and browser code do not own database schema decisions. Selectors are centralized. Configuration uses Pydantic Settings. These choices make YouTube-specific breakage less likely to contaminate persistence and review logic.

One area to watch is orchestration concentration in `cli.py`. As enrichment, retries, exports, backups, and semantic search are added, command functions should remain thin and delegate to services.

## Requirement coverage

| Requirement | Status | Evidence and gap |
| --- | --- | --- |
| Collect available Liked Videos | Mostly complete | A real large read-only crawl completed on the current lockup layout. Hidden unavailable entries without a usable video ID prevent full header-count reconciliation. Boundary samples remain to be checked. |
| Collect every saved playlist | Mostly complete | One complete account-wide read-only crawl discovered 85 playlists and isolated 19 count mismatches. Intermittent four-card discovery is blocked from full writes by an exact expected-count guard. Representative mismatches and a repeatable full local import remain. |
| Optimize the saved library | Complete baseline | Local analysis reports duplicate regular placement, empty and oversized playlists, uncategorized videos, and missing approved additions. Recommendations are add only and require later explicit apply authorization. |
| Avoid YouTube Data API for bulk work | Complete | Collection and playlist assignment use Playwright only. |
| Reuse authenticated browser session | Complete for reads | Normal Chrome login is confirmed. Sync starts the same branded browser and profile, attaches through loopback-only CDP, and completed repeated authenticated read-only crawls. Playlist-write reuse remains untested. |
| Store data in SQLite | Complete | Normalized video, playlist, membership, classification, and action models plus Alembic migrations are present. |
| Deterministic categorization | Complete | Priority-ordered keyword, regex, channel, and multi-category rules are implemented. |
| Optional AI categorization | Complete baseline | Providers are disabled by default, preview is deterministic-only, zero disables AI calls, and write mode has timeouts, bounded retries, a persisted daily token ceiling, cost recording, and loopback restriction for local endpoints. Live provider validation is optional and private. |
| Multiple categories per video | Complete | `video_categories` implements many-to-many assignments. |
| Review uncertain results | Complete | Low-confidence proposals and unclassified videos are exposed for manual action in Streamlit. |
| Add videos to playlists | Partial | ID-aware add-only automation, validation-only dialog inspection, inventory recheck, and already-present handling are implemented. A controlled live add is pending. |
| Resume safely and idempotently | Complete baseline | Sync runs, action keys, per-discovery commits, transcript upserts, retry state, interrupted synchronization and action recovery, and the single-writer lock are durable. |
| Later synchronization processes new or changed videos | Complete in design | Crawlers fingerprint video metadata and upsert stable playlist memberships. Only new or changed videos return to pending classification. A full write-enabled library import remains to validate persistence at account scale. |
| Search and filtering | Complete | Local text search and approved-category filtering are implemented. |
| Summaries | Basic | Local deterministic summaries use description or transcript text. No generative summary provider or persistent summary versioning exists. |
| Eventual semantic search | Planned boundary | A privacy-safe status interface exists. Embeddings and vector indexing are not implemented. |
| Structured logging | Complete baseline | Structlog JSON output is configured. File rotation and retention are not needed yet because logs remain console-only. |
| Cross-platform operation | Partial | Windows and shell scripts exist. The primary validation platform is Windows. |
| Streamlit interface | Complete baseline | Required workflow pages, collection progress, service boundaries, and locked mutations exist. Bulk review is not implemented. |

## Data model assessment

The schema covers the required entities and operational state. Unique YouTube video and playlist IDs prevent duplicate identities. Composite membership constraints preserve one row per playlist and video while `active` retains historical absence. Composite assignment constraints preserve classification provenance. Classification runs retain provider evidence. Browser action keys protect against duplicate planned writes. Foreign keys are enabled for SQLite connections.

Current data risks:

1. Content fingerprints cover collected playlist metadata but do not version every future enrichment input.
2. `raw_metadata`, transcript text, and AI raw responses can grow materially. Counts-only inventory exists, but destructive retention and field-level export policies are not implemented.
3. SQLite remains a single-user system. The application lock prevents cooperating app writers but cannot control unrelated external SQLite clients.
4. A complete saved-library import can create a large membership table. Query performance needs measurement against the current full account inventory.
5. Transcript retry eligibility is stored, but automatic enforcement of retry timing and limits remains incomplete.

## Browser automation assessment

Safety behavior is correctly conservative. Manual authentication runs in normal Chrome or Edge without Playwright or remote debugging. Automated work starts the same dedicated profile and attaches over an ephemeral debugging port bound only to `127.0.0.1`. The application does not accept passwords, checks for security interruptions, and throttles actions. Playlist operations are add-only. Dry-run is the default.

Primary browser risks:

1. YouTube selectors support the observed English classic and lockup layouts but may fail under future experiments, localization, accessibility changes, or new renderer components.
2. Current large Liked Videos and complete saved-library crawls ran, but hidden unavailable entries, 19 playlist count mismatches, and representative boundary checks still prevent full completeness reconciliation.
3. CAPTCHA and challenge detection is necessarily heuristic. Unknown prompts must fail closed.
4. Transcript access varies by video, language, availability, and layout. Current extraction is best-effort.
5. Playlist matching requires an exposed exact ID when one is configured. Name-only matching is allowed only without a configured ID and requires one exact unambiguous name. Missing IDs, mismatches, and ambiguous names fail closed.
6. There is no saved diagnostic snapshot workflow for selector failures. Any future capture must be sanitized before it can enter Git.
7. Account-wide crawling is sequential and can take substantial time. Progress, cooperative cancellation, durable run state, and a single-writer lock reduce but do not remove that cost.
8. Playlist cards with missing, localized, or experimental metadata may be discovered without a reliable displayed count. The crawler must prefer actual collected membership over an inferred count.
9. The Playlists page intermittently presents only four cards with no continuation even though a separate run discovered 85. An unrestricted write therefore requires an exact expected count from a recent preview and stops before playlist processing on mismatch.

YouTube playlist hydration is intermittently slow even after navigation commits. The collector now makes three bounded attempts. Each attempt repeats login and security checks, and the final failure is sanitized and actionable. A repeated authenticated read-only crawl succeeded after this change.

Live validation must not begin with write mode. Start with `ykm sync-library --limit-playlists 3`, then run the complete `ykm sync-library` preview. Inspect playlist discovery and representative counts before `ykm sync-library --write --expect-playlists <verified-count>`. Never lower the expected count to accept a partial discovery. Generate and inspect an optimization report and playlist plan before any `apply-plan --apply` operation.

## Classification and review assessment

Deterministic rules are the preferred first pass because they are predictable, cheap, local, and auditable. Multiple matching categories are supported. Confidence controls automatic approval. Manual decisions remain distinguishable from rule and AI assignments.

AI is correctly optional. However, enabling a remote provider can send titles, descriptions, channels, and transcript content outside the machine. Provider use needs a clear operator decision, private API-key configuration, cost visibility, and retention review.

Classification gaps:

- Timeouts, bounded retries, a daily token ceiling, loopback local-provider enforcement, and estimated cost are implemented. Retry jitter, a circuit breaker, and per-run cost ceilings remain.
- Prompt and output tests do not yet cover every malformed, adversarial, timeout, and rate-limit response.
- Conflict review is confidence-based. There is no explicit mutually-exclusive category policy.
- Learning currently reports manual category frequency and does not generate safe draft rules.
- Rule changes do not trigger a controlled reclassification/version migration workflow.

## Search and knowledge-management assessment

The current text search is suitable for a small or moderate library. It searches title, description, and channel and supports category filtering. Local summaries do not call an external service. Saved-playlist membership materially improves organization context, but search does not yet filter directly by imported playlist.

For larger libraries, SQLite FTS5 should replace `%LIKE%` scans. Transcript search should have explicit inclusion controls because transcripts can be large. Semantic search should remain provider-neutral and local-first. A local embedding option, model/version tracking, chunk hashes, and incremental index invalidation are required before implementation is considered complete.

## Security and privacy assessment

Current controls are appropriate:

- No password fields or password persistence.
- Dedicated browser profile instead of exported cookies.
- Private runtime state excluded from Git and Docker build contexts.
- AI disabled by default.
- Destructive YouTube operations are absent.
- Playlist additions require explicit apply mode.
- Security prompts stop automation.

Remaining controls to add before broader use:

- Add retention settings and field-level sanitized export for transcripts, raw metadata, and AI responses. The current inventory is counts only.
- Add privacy-safe selector diagnostics that never capture personal page content by default.
- Consider optional database encryption only if it can fail closed and avoid silent plaintext fallback.

## Test assessment

The current 72-test suite verifies pure logic, persistence, playlist and membership upserts, complete versus incomplete deactivation, expected library-count enforcement, interrupted run recovery, optimization, planning idempotency and inventory suppression, review rejection, transcript retry state, database recovery, locks, CLI boundaries, Streamlit startup, migrations, environment-targeted Alembic execution, AI preview and zero-budget enforcement, scrolling, URL normalization, hydration retry, continuation discovery, recommendation exclusion, fail-closed security handling, playlist dialog resolution, and browser process boundaries. Coverage is 77.62% against a 75% floor.

Important remaining tests:

1. More AI timeout, rate-limit, malformed-response, and circuit-breaker cases.
2. Retry-time and retry-limit enforcement for enrichment.
3. Rule-version and controlled-reclassification behavior when implemented.
4. A separately invoked live validation suite that can never run automatically in CI.

## Operational readiness

| Area | Rating | Reason |
| --- | --- | --- |
| Architecture | 5/5 | Boundaries, explicit write controls, recovery, locking, and privacy contracts are coherent and tested. |
| Persistence | 5/5 | Normalized schema, constraints, migrations, single-writer protection, integrity checks, verified backup, and restore are present. |
| Browser collection | 4/5 | Mocked critical paths and current full read-only evidence are strong. Nineteen playlist mismatches, hidden Liked entries, and intermittent partial library discovery remain. |
| Playlist writes | 4/5 | ID-aware fail-closed execution, validation-only inspection, inventory recheck, and recovery are tested. One controlled live add remains. |
| Classification | 4/5 | Rules and optional AI are usable with timeout, retry, token, and cost controls. Rule versions and broader provider fault tests remain. |
| Review UI | 4/5 | Required decisions, rejection recovery, progress, and library optimization are available. Bulk review remains future work. |
| Search | 3/5 | Good basic local search. FTS and semantic indexing remain. |
| Privacy and safety | 5/5 | Strong defaults, exclusions, lock discipline, private-file CI, counts-only inventory, and verified private backups are present. |
| Automated tests | 5/5 | 72 tests pass with 77.62% coverage, strict typing, security lint, dependency audit, migration checks, and mocked critical browser paths. |
| Documentation | 5/5 | Detailed setup, first-run, routine use, configuration, CLI, UI, safety, troubleshooting, development, changelog, and assessment guidance are present. |
| Overall production readiness | 4/5 | Production-candidate code. Playlist mismatches, a repeatable full local import, representative Liked Videos reconciliation, and one explicitly approved disposable-playlist add are mandatory before 5/5. |

## Prioritized work

The detailed working backlog, upgrade IDs, dependencies, and acceptance criteria are maintained in local-only `future-upgrades.md`. The priorities below remain the assessment-level summary. Completed items are recorded in tracked [completed-upgrades.md](completed-upgrades.md).

### Priority 0: prove safe collection

1. Diagnose why some Playlists sessions expose only four cards while another exposes 85.
2. Reconcile the 19 failed playlist counts and the two severe observed shortfalls without admitting recommendation rows.
3. Reconcile representative empty, small, medium, and large playlist counts.
4. Reconcile hidden unavailable entries where YouTube reports them.
5. Record failed or private playlists without committing personal video data or raw browser state.
6. Run `ykm sync-library --write --expect-playlists <verified-count>` only after the preview is credible, then repeat it and verify idempotent local rows.
7. Add sanitized mocked fixtures and regression tests for every discovered layout issue.

### Priority 1: harden browser and resume behavior

1. Add selector diagnostics that report the failing logical selector without storing page content by default.
2. Enforce enrichment retry timing and limits.
3. Validate add-only playlist behavior on one disposable test playlist before any bulk operation.

### Priority 2: strengthen operations

1. Complete classification and action progress surfaces.
2. Add retention controls and a field-level sanitized export after the current counts-only inventory.
3. Add AI retry jitter, circuit breaking, per-run ceilings, and broader provider fault tests.
4. Add rule-version tracking and controlled reclassification.

### Priority 3: improve knowledge retrieval

1. Add SQLite FTS5 for titles, descriptions, channels, and opt-in transcripts.
2. Add summary versioning and regeneration controls.
3. Design local-first chunking and embedding storage.
4. Implement semantic search only after privacy, model-version, and incremental-index behavior are documented and tested.

## Release gates

Do not call the project production-ready until all of the following are true:

- Pending: A fresh full real Liked Videos crawl reconciles available count and representative boundary samples.
- Partial: A complete read-only saved-playlist crawl discovered 85 playlists, but 19 count mismatches and intermittent four-card discovery remain.
- Pending: A write-enabled saved-library import protected by the expected-count guard is completed, repeated, and creates no duplicate playlist or membership rows.
- Complete: Interrupted collection preserves committed discoveries and records terminal run state.
- Complete in mocked validation: Login, CAPTCHA, consent, and security prompts fail closed.
- Pending: One controlled playlist addition is verified as target-correct, already-present safe, and duplicate-free.
- Complete: Mocked browser selector regressions cover the known live layouts and critical workflows.
- Complete: Transcript enrichment upserts one row and records retry state.
- Complete: Integrity, backup, restore, and migration backup are documented and tested.
- Complete: CLI and service dry-run/write boundaries have integration coverage.
- Pending: One full synchronization, classification, review, planning, validation, and controlled apply cycle completes successfully.
- Complete: Automated tests confirm no private runtime file category is tracked, and the current worktree contains no unignored private runtime artifact.

## Mandatory change workflow

For every repository change:

1. Read this assessment before implementation.
2. Confirm the requested change does not weaken dry-run, privacy, or add-only guarantees.
3. Implement the smallest complete change through the correct architectural layer.
4. Add or update tests proportional to the changed risk.
5. Run Ruff, strict mypy, and all non-live tests.
6. Update `CHANGELOG.md` with every delivered change.
7. Update `README.md` when setup, commands, behavior, status, or scope changes.
8. Update this assessment when evidence, coverage, risk, readiness, or priorities change.
9. If a `future-upgrades.md` item shipped, preserve its ID, remove it from the future ledger, and add the verified result to `completed-upgrades.md`.
10. Confirm the same upgrade is not listed as both future and completed.
11. Confirm private runtime files and `future-upgrades.md` remain excluded before staging.
