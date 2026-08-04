# Project assessment

## Assessment metadata

| Item | Current value |
| --- | --- |
| Project | YouTube Knowledge Manager |
| Package | `youtube_knowledge_manager` |
| Version | 0.1.0 |
| Assessment date | 2026-08-04 |
| Lifecycle | Alpha |
| Primary platform | Windows 11 |
| Supported runtime | Python 3.12 or newer |
| System of record | Local SQLite database |
| Live YouTube validation | Not yet completed |
| Overall readiness | Ready for controlled local dry-run validation. Not ready for unattended playlist writes. |

Read this file before changing the project. Update it in the same change set whenever implementation, tests, documentation, risks, readiness, or priorities change.

## Executive assessment

The project has a coherent initial architecture and a working local application foundation. Persistence, configuration, browser boundaries, synchronization, deterministic classification, optional AI classification, human review, playlist planning, search, CLI operations, Streamlit pages, migration support, structured logging, scripts, tests, and documentation are implemented.

The strongest design decision is the separation between read operations, local persistence, planning, and browser writes. YouTube changes require explicit `--apply` authorization. Every proposed playlist addition receives a stable idempotency key and durable attempt state. The code does not implement playlist deletion, removal from Liked Videos, or playlist removal.

The largest gap is live browser validation. The Playwright adapters are implemented, but the project has not yet been exercised against Mick's authenticated YouTube account. YouTube DOM, localization, experiments, consent state, playlist size, virtualized scrolling, transcript availability, and account-security prompts can all affect real behavior. The application must remain in dry-run mode until collection completeness and write idempotency are proven with controlled live tests.

The current code quality baseline is good for an alpha. Ruff, strict mypy, the non-live pytest suite, migration execution, schema drift detection, CLI initialization, and privacy-file checks pass. Test depth is not yet sufficient for production browser automation. Browser tests currently cover parsing but do not simulate a complete Liked Videos crawl, security interruption, transcript interaction, or playlist dialog.

Upgrade tracking now has a permanent tracked completion ledger and a local-only future backlog. The local backlog contains actionable ideas derived from this assessment. When an item ships, its stable ID and actual verification evidence move to `completed-upgrades.md`; it must not remain in both ledgers.

## Verified baseline

The following checks passed on Windows with Python 3.12.13:

| Check | Result |
| --- | --- |
| Dependency resolution | `uv sync --all-extras` completed and generated `uv.lock` |
| Ruff lint | Passed |
| Ruff format check | Passed |
| Strict mypy | Passed across 53 source files |
| Pytest | 9 passed, live YouTube tests excluded |
| Initial Alembic migration | Passed against a temporary SQLite database |
| Alembic schema drift | No new upgrade operations detected |
| CLI initialization | `ykm init-db` passed |
| CLI discovery | All expected commands appeared in `ykm --help` |
| Private runtime files | No database, browser profile, cookie, storage-state, transcript, or `.env` file was a Git candidate |
| Operator documentation | README verified against current CLI help, settings, scripts, safety boundaries, and Streamlit workflow |
| Upgrade tracking | `completed-upgrades.md` is tracked; root `future-upgrades.md` is local-only and ignored by Git |
| Live account crawl | Not run |
| Live playlist write | Not run |

Validation commands:

```powershell
uv sync --all-extras
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -m "not live_youtube"
uv run alembic upgrade head
uv run ykm --help
```

## Architecture assessment

### Boundaries

| Layer | Responsibility | Assessment |
| --- | --- | --- |
| `browser` | Persistent profile, safety detection, selectors, crawling, details, transcripts, playlist interaction | Correct boundary. High external volatility. Needs live and mocked coverage. |
| `collection` | Fingerprints, immediate persistence, enrichment, synchronization run tracking | Good incremental design. Enrichment resume behavior needs strengthening. |
| `db` | SQLAlchemy models, sessions, repositories, normalized persistence | Strong baseline. SQLite is appropriate for local single-user use. |
| `classification` | YAML schemas, deterministic rules, AI provider contract, provider adapters, result validation | Good separation. Provider cost calculation and retry policy are incomplete. |
| `planning` | Durable, idempotent playlist proposals and controlled execution | Strong safety model. Exact-name playlist resolution needs live validation. |
| `search` | Text search, category filtering, local summaries, semantic-search boundary | Suitable alpha implementation. LIKE queries will eventually need FTS5. |
| `services` | Application workflows consumed by CLI and UI | Correct direction. Some service queries can be optimized before large libraries. |
| `ui` | Streamlit presentation and explicit user decisions | Useful initial interface. Long-running browser tasks need better progress and cancellation handling. |
| `cli` | Operator workflow and explicit write controls | Clear and practical. Command-level integration coverage is limited. |

### Dependency direction

The UI calls services and repositories rather than embedding SQL. Planning and browser code do not own database schema decisions. Selectors are centralized. Configuration uses Pydantic Settings. These choices make YouTube-specific breakage less likely to contaminate persistence and review logic.

One area to watch is orchestration concentration in `cli.py`. As enrichment, retries, exports, backups, and semantic search are added, command functions should remain thin and delegate to services.

## Requirement coverage

| Requirement | Status | Evidence and gap |
| --- | --- | --- |
| Collect available Liked Videos | Partial | Progressive scrolling and extraction are implemented. Completeness is not proven against a real large playlist. Unavailable entries without a usable video ID may not be representable. |
| Avoid YouTube Data API for bulk work | Complete | Collection and playlist assignment use Playwright only. |
| Reuse authenticated browser session | Complete in code | Dedicated persistent profile and manual login command exist. Live validation remains. |
| Store data in SQLite | Complete | Normalized SQLAlchemy models and Alembic migration are present. |
| Deterministic categorization | Complete | Priority-ordered keyword, regex, channel, and multi-category rules are implemented. |
| Optional AI categorization | Complete in code | OpenAI and local compatible providers exist and are disabled by default. No provider integration test has run. |
| Multiple categories per video | Complete | `video_categories` implements many-to-many assignments. |
| Review uncertain results | Complete | Low-confidence proposals and unclassified videos are exposed for manual action in Streamlit. |
| Add videos to playlists | Partial | Add-only automation and already-present detection are implemented. Live playlist dialogs have not been validated. |
| Resume safely and idempotently | Mostly complete | Sync runs and stable browser-action keys are durable. Collection stores each discovery immediately. Enrichment checkpoints and transcript retries need improvement. |
| Later synchronization processes new or changed videos | Complete in design | The crawler observes the playlist and fingerprints metadata. Only new or changed rows return to pending classification. Full-list scrolling is still required to prove completeness. |
| Search and filtering | Complete | Local text search and approved-category filtering are implemented. |
| Summaries | Basic | Local deterministic summaries use description or transcript text. No generative summary provider or persistent summary versioning exists. |
| Eventual semantic search | Planned boundary | A privacy-safe status interface exists. Embeddings and vector indexing are not implemented. |
| Structured logging | Complete baseline | Structlog JSON output is configured. File rotation and retention are not needed yet because logs remain console-only. |
| Cross-platform operation | Partial | Windows and shell scripts exist. The primary validation platform is Windows. |
| Streamlit interface | Complete baseline | Required workflow pages exist. Browser-task progress and cancellation need work. |

## Data model assessment

The schema covers the required entities and operational state. Unique YouTube IDs prevent duplicate videos. Composite assignment constraints preserve assignment provenance. Classification runs retain provider evidence. Browser action keys protect against duplicate planned writes. Foreign keys are enabled for SQLite connections.

Current data risks:

1. Transcript enrichment creates a new transcript row per attempt. Re-running the same language and generation type can violate the composite unique constraint instead of updating the existing transcript.
2. Content fingerprints cover collected playlist metadata but not every future enrichment field. Fingerprint versioning will be needed when the input set changes.
3. `raw_metadata` and AI raw responses can grow materially. Retention and export policies are not defined.
4. SQLite supports the expected single-user workload, but concurrent Streamlit and CLI writers can still contend despite the busy timeout.
5. No first-class backup, restore, integrity-check, or schema-version export command exists.

## Browser automation assessment

Safety behavior is correctly conservative. The browser uses a dedicated profile, does not accept passwords, checks for security interruptions, and throttles actions. Playlist operations are add-only. Dry-run is the default.

Primary browser risks:

1. YouTube selectors are based on a current English desktop layout and may fail under experiments, localization, accessibility changes, or new renderer components.
2. The Liked Videos page uses virtualized content. Stable-count termination must be proven on the full real playlist, including very large libraries.
3. CAPTCHA and challenge detection is necessarily heuristic. Unknown prompts must fail closed.
4. Transcript access varies by video, language, availability, and layout. Current extraction is best-effort.
5. Playlist matching uses exact visible names. Duplicate, truncated, localized, or renamed playlists can cause lookup failures.
6. There is no saved diagnostic snapshot workflow for selector failures. Any future capture must be sanitized before it can enter Git.

Live validation must not begin with write mode. The first run should use a dedicated profile and `ykm sync` without `--write`. Inspect counts and samples before running `ykm sync --write`. Generate a playlist plan and inspect it before any `apply-plan --apply` operation.

## Classification and review assessment

Deterministic rules are the preferred first pass because they are predictable, cheap, local, and auditable. Multiple matching categories are supported. Confidence controls automatic approval. Manual decisions remain distinguishable from rule and AI assignments.

AI is correctly optional. However, enabling a remote provider can send titles, descriptions, channels, and transcript content outside the machine. Provider use needs a clear operator decision, private API-key configuration, cost visibility, and retention review.

Classification gaps:

- No AI retry, timeout, circuit-breaker, or daily cost ceiling exists.
- Estimated cost is modeled but not calculated.
- Prompt and output tests do not cover malformed or adversarial provider responses.
- Conflict review is confidence-based. There is no explicit mutually-exclusive category policy.
- Learning currently reports manual category frequency and does not generate safe draft rules.
- Rule changes do not trigger a controlled reclassification/version migration workflow.

## Search and knowledge-management assessment

The current text search is suitable for a small or moderate library. It searches title, description, and channel and supports category filtering. Local summaries do not call an external service.

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

- Document OS-level protection and backup expectations for the browser profile and SQLite database.
- Add a local data inventory and retention settings for transcripts and raw AI responses.
- Add an export command that excludes authentication state by construction.
- Add database integrity checking and an operator-confirmed backup command before migrations.
- Consider optional database encryption only if it can fail closed and avoid silent plaintext fallback.

## Test assessment

The current nine-test suite verifies core pure logic, persistence, planning idempotency, search, and migration creation. Strict static typing and linting reduce common implementation errors.

Important missing tests:

1. Mocked progressive scrolling with recycled playlist DOM nodes.
2. Immediate persistence when a crawl is interrupted.
3. CAPTCHA, consent, login, and security-challenge fail-closed behavior.
4. Already-present and missing-playlist dialog behavior.
5. Playlist execution retry and resume after a partial failure.
6. Low-confidence, conflicting, rejected, and unclassified review flows.
7. AI response validation, timeout, error, and invalid-category handling.
8. Transcript upsert and retry behavior.
9. CLI dry-run and explicit-write integration tests.
10. Streamlit service-boundary smoke tests.
11. A separately invoked live validation suite that cannot run in CI.

## Operational readiness

| Area | Rating | Reason |
| --- | --- | --- |
| Architecture | 4/5 | Clear boundaries and safe workflow. Some orchestration and enrichment work remains. |
| Persistence | 4/5 | Normalized schema, repositories, migration, and constraints are present. Backup and transcript retry need work. |
| Browser collection | 2/5 | Implemented but not live validated. This is the highest uncertainty. |
| Playlist writes | 2/5 | Safe and idempotent design, but real dialog behavior is unverified. |
| Classification | 3/5 | Rules are usable. AI operations and reclassification controls need maturity. |
| Review UI | 3/5 | Required decisions are available. Bulk review and progress handling are limited. |
| Search | 3/5 | Good basic local search. FTS and semantic indexing remain. |
| Privacy and safety | 4/5 | Strong defaults and exclusions. Retention, backup, and optional encryption need definition. |
| Automated tests | 3/5 | Core logic is covered and all checks pass. Browser workflow coverage is thin. |
| Documentation | 5/5 | Detailed setup, first-run, routine use, configuration, CLI, UI, safety, troubleshooting, development, changelog, and assessment guidance are present. |
| Overall production readiness | 2/5 | Appropriate for controlled alpha validation, not unattended operation. |

## Prioritized work

The detailed working backlog, upgrade IDs, dependencies, and acceptance criteria are maintained in local-only `future-upgrades.md`. The priorities below remain the assessment-level summary. Completed items are recorded in tracked [completed-upgrades.md](completed-upgrades.md).

### Priority 0: prove safe collection

1. Install Chromium through the bootstrap script and create a dedicated profile.
2. Run `ykm browser-login` and authenticate manually.
3. Run a read-only `ykm sync` against the real Liked Videos playlist.
4. Compare collected counts and representative first, middle, and last entries with the visible playlist.
5. Record any selector or termination failures without committing personal video data or raw browser state.
6. Add sanitized mocked fixtures and regression tests for every discovered layout issue.

### Priority 1: harden browser and resume behavior

1. Add complete mocked browser-flow tests.
2. Add selector diagnostics that report the failing logical selector without storing page content by default.
3. Change transcript enrichment to upsert and record retry state.
4. Add enrichment checkpoints and explicit failure recovery.
5. Add a single-writer lock for synchronization and playlist execution.
6. Validate add-only playlist behavior on one disposable test playlist before any bulk operation.

### Priority 2: strengthen operations

1. Add database integrity, backup, restore, and migration preflight commands.
2. Add sync and action progress reporting with cancellation support.
3. Add structured summary reports that contain no private data unless explicitly exported locally.
4. Add AI timeout, retry, cost calculation, and configurable spending ceilings.
5. Add rule-version tracking and controlled reclassification.

### Priority 3: improve knowledge retrieval

1. Add SQLite FTS5 for titles, descriptions, channels, and opt-in transcripts.
2. Add summary versioning and regeneration controls.
3. Design local-first chunking and embedding storage.
4. Implement semantic search only after privacy, model-version, and incremental-index behavior are documented and tested.

## Release gates

Do not call the project production-ready until all of the following are true:

- A full real Liked Videos crawl completes with verified count and boundary samples.
- Interrupted collection resumes without losing already-discovered videos.
- Security prompts fail closed in mocked and controlled live validation.
- A playlist addition is verified as already-present safe and duplicate-free.
- Browser selector regression tests cover the live layout.
- Transcript enrichment is idempotent.
- Backup and restore are documented and tested.
- CLI and service dry-run/write boundaries have integration coverage.
- At least one full synchronization, classification, review, planning, and controlled apply cycle completes successfully.
- No personal YouTube data, browser state, database, transcript, cookie, or secret is a Git candidate.

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
