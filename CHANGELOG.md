# Changelog

Every repository change is recorded in this file. Entries describe behavior, code, configuration, tests, documentation, and operational changes. Dates use `YYYY-MM-DD`.

## Unreleased

### Added

- Added an exact `--expect-playlists` release guard for unrestricted saved-library writes. A discovery mismatch now stops before any individual playlist is processed.
- Added interrupted synchronization-run recovery so a terminated write is marked failed before the next write begins.
- Added support for YouTube's current `yt-continuation-item-view-model` continuation element and fail-closed reconciliation against the playlist header count.
- Added a production-hardening release gate with a 75% coverage floor, Bandit security scanning, frozen dependency auditing, Alembic upgrade/check/downgrade validation, and tracked private-file tests.
- Added a single-writer application lock for browser, synchronization, enrichment, planning, migration, backup, restore, and UI mutation workflows, plus explicit stale-lock recovery.
- Added `db-check`, verified `db-backup`, guarded `db-restore`, and automatic verified backups before migrations and restores.
- Added resumable metadata and transcript enrichment with unique-row upserts, attempt state, retry eligibility, batch progress, and the `enrich` command.
- Added `apply-plan --validate` to verify real Save-dialog targets without selecting a playlist or mutating action state.
- Added `data-inventory` with counts-only console and atomic JSON output.
- Added AI provider timeouts, bounded retries, daily token limits, operator-configured cost rates, and loopback-only local provider validation.
- Added mocked coverage for scrolling, incomplete-crawl preservation, login and security stops, playlist ID resolution, duplicate names, already-present actions, interrupted execution, lock behavior, database recovery, enrichment, review rejection, CLI boundaries, Streamlit startup, and private-file exclusions.
- Added saved playlist discovery from YouTube's Playlists page, including stable IDs, names, canonical URLs, displayed counts, and Liked Videos and Watch Later system identification.
- Added generic per-playlist video collection and the `sync-library` command with dry-run default, optional playlist limit, resumable local persistence, and per-playlist failure isolation.
- Added `youtube_playlists` and `playlist_memberships` models, repositories, indexes, relationships, and an Alembic migration for current and historical saved playlist membership.
- Added local library optimization metrics for empty and oversized regular playlists, duplicate regular-playlist placement, uncategorized saved videos, and missing approved category additions.
- Added the `optimize-library` command and Library Optimization Streamlit page. Both remain local and produce only add-only recommendations.
- Added saved-playlist scope and playlist limits to the Streamlit Collection page and a saved-playlist count to the dashboard.
- Added tests for playlist discovery normalization, displayed counts, membership idempotency and deactivation, optimizer calculations, migration creation, and planning against known membership.
- Added an external browser launcher that locates Chrome or Edge, starts the dedicated profile, reserves an ephemeral loopback debugging port, and connects Playwright over CDP.
- Added unit coverage for dedicated profile arguments, loopback-only debugging, normal manual login, and headless browser mode.
- Added normalization coverage for the current Liked Videos lockup markup and Shorts URLs.
- Added `assessment.md` as the required pre-change project baseline, architecture assessment, requirement coverage matrix, verification record, risk register, and prioritized work list.
- Added this changelog and the requirement to record every delivered repository change.
- Added tracked `completed-upgrades.md` as the permanent ledger for shipped project upgrades and their verification evidence.
- Added local-only `future-upgrades.md` with prioritized, project-specific upgrade ideas and measurable acceptance criteria.

### Changed

- Upgraded the GitHub Actions checkout and uv setup actions to Node.js 24 releases and pinned their full commit SHAs.
- Changed collected playlist positions to count only verified membership rows, preventing recommendation elements from creating position gaps.
- Changed lock-file creation to request owner-only permissions and changed dashboard playlist totals to use a direct count query.
- Changed AI budgeting so a zero daily limit disables provider calls and preview classification is deterministic-only, preventing unrecorded provider usage from bypassing the daily ceiling.
- Corrected playlist target documentation to require an exposed matching ID whenever an ID is configured; exact-name matching is used only when no ID is configured.
- Changed raw Alembic execution to honor `YKM_DATABASE_URL`, ensuring CI and operator migration checks target the configured database, and made CI dependency installation frozen.
- Changed CLI safety tests to assert rejected side effects instead of platform-dependent Rich terminal rendering, making the suite stable on Windows and Linux.
- Scoped playlist item extraction to the primary page content and rejected video links whose `list` parameter does not match the playlist being crawled, excluding recommendation rows from membership inventory.
- Increased external browser CDP connection attempts to a bounded five-second per-attempt timeout while retaining the 30-second overall startup deadline.
- Changed saved-library summaries to report discovery completeness and the full discovered count separately from the processed count.
- Changed playlist membership deactivation to require a complete crawl and displayed-count reconciliation. Failed, interrupted, limited, or mismatched crawls preserve prior active memberships.
- Changed playlist execution to prefer configured playlist IDs, fail closed on ID mismatches, reject ambiguous duplicate names, recheck imported membership before browser startup, and recover abandoned running actions.
- Changed rejected-only classifications to return to review instead of disappearing from the queue.
- Removed the silent 10,000-row cap from approved-assignment planning.
- Changed normal commands to require a current database revision instead of migrating implicitly.
- Changed Windows scripts to keep the uv environment under `%LOCALAPPDATA%` in copy mode, avoiding OneDrive virtual-environment corruption.
- Updated GitPython to 3.1.59, pytest to 9.1.1, and pytest-asyncio to 1.4.0. The frozen dependency audit reports no known vulnerabilities.
- Refactored Liked Videos collection onto the reusable playlist video collector without changing the existing `ykm sync` workflow.
- Changed playlist planning to skip approved additions already known through an active imported playlist membership.
- Changed limited library previews to prioritize small regular playlists with known counts instead of large system playlists.
- Changed empty-playlist synchronization to deactivate previously active local memberships after a successful zero-count observation.
- Excluded Liked Videos and Watch Later from oversized-playlist optimization results.
- Increased approved-assignment retrieval capacity for library-scale planning.
- Documented the all-playlist import, optimization report, local schema, safety boundaries, CLI commands, Streamlit pages, failure behavior, and full-library validation gate.
- Updated package metadata and privacy guidance to cover saved playlist names and membership data.
- Updated the assessment, completed-upgrade ledger, local future backlog, and agent rules for advisory, add-only library optimization.
- Changed `browser-login` to start normal Chrome or Edge without Playwright or remote debugging so Google authentication is not attempted through an automated browser window.
- Changed authenticated browser operations to start the branded browser first and attach Playwright afterward, preserving the dedicated profile's signed-in state.
- Changed the default browser channel from bundled Chromium to installed Chrome and raised the Playwright minimum to 1.62 for the CDP connection controls used by the project.
- Documented the corrected login and synchronization workflow, loopback debugging boundary, profile-lock recovery, and signed-out-session troubleshooting.
- Updated the assessment and completed-upgrade ledger with the authenticated browser-session fix and its verification evidence. Full live crawl validation remains pending.
- Updated Liked Videos collection to support both the classic playlist renderer and YouTube's current lockup view model, including watch, Shorts, and live URLs.
- Replaced per-element Playwright calls with one bulk extraction per visible batch, eliminating quadratic reparsing on large playlists.
- Separated navigation and action timeouts, used navigation commit instead of delayed DOM-content completion, and allowed playlist rows more time to hydrate.
- Added three bounded playlist-hydration attempts, YouTube Sign in link detection, fail-closed retry checks, and an actionable final load error.
- Added mocked coverage for successful hydration retry and immediate stop when a retry detects sign-in.
- Completed a real authenticated read-only crawl with zero local or YouTube writes. Exact personal library counts remain excluded from tracked files, and hidden unavailable entries still require reconciliation.
- Repeated the authenticated read-only crawl successfully after adding hydration retry handling.
- Updated `AGENTS.md` to require future agents to read `assessment.md` before making changes.
- Updated `AGENTS.md` to require `CHANGELOG.md`, `README.md`, and `assessment.md` to be reviewed and updated in every change set, including documentation-only changes.
- Replaced the short README setup notes with a complete Windows-first operator guide covering prerequisites, bootstrap behavior, manual setup, first-run validation, routine synchronization, exact read/write boundaries, configuration, categories, rules, optional AI providers, every CLI command and flag, Streamlit pages, private data locations, migrations, Docker, troubleshooting, testing, privacy checks, known limitations, and change control.
- Corrected the setup workflow to state that the bootstrap scripts already create private configuration files when missing, install Chromium, and apply migrations.
- Documented that `sync --write` writes locally and classifies but does not change YouTube, while `apply-plan --apply` is the only command that performs YouTube playlist writes.
- Added a controlled one-item playlist validation procedure before any larger apply batch.
- Clarified that `YKM_DRY_RUN` is not write authorization and that each CLI or UI operation still requires its explicit write control.
- Documented the current requirement to supply `OPENAI_API_KEY` through the starting process environment instead of relying on `.env` loading.
- Documented Docker initialization with `ykm init-db` so the mounted database receives both migrations and category synchronization.
- Updated `assessment.md` to record the expanded operator documentation and current documentation-readiness rating.
- Added a root `.gitignore` rule for `future-upgrades.md` so planning ideas remain local and cannot be staged normally.
- Updated `AGENTS.md`, `README.md`, and `assessment.md` with the mandatory upgrade lifecycle: preserve the upgrade ID, remove shipped work from the future ledger, add it to the completed ledger, and verify the two files do not disagree.
- Linked `completed-upgrades.md` from the README and documented how to verify that the future ledger remains ignored.

## 0.1.0 - 2026-08-03

### Added

#### Repository and governance

- Created the Python 3.12+ `youtube_knowledge_manager` package and `ykm` command-line entry point.
- Added project-specific `AGENTS.md` instructions covering architecture, safety, privacy, tests, selectors, dry-run behavior, and documentation.
- Added MIT license metadata, Python packaging configuration, dependency locking, Make targets, environment examples, Docker configuration, and GitHub Actions CI.
- Added `.gitignore` and `.dockerignore` protections for secrets, browser state, cookies, databases, transcripts, generated reports, and personal YouTube data.

#### Persistence and migrations

- Added SQLAlchemy 2.x models for videos, transcripts, hierarchical categories, video-category assignments, classification runs, classification rules, synchronization runs, and browser actions.
- Added unique constraints, foreign keys, status enums, timestamps, content fingerprints, raw metadata storage, and idempotency keys.
- Added SQLite foreign-key enforcement and a busy timeout on every application connection.
- Added repository abstractions for videos, categories, classification assignments, synchronization runs, and browser actions.
- Added an Alembic environment and the initial normalized database migration.

#### Browser automation and collection

- Added dedicated persistent Chromium profile validation and session management.
- Added centralized YouTube selectors.
- Added detection and hard stops for login pages, CAPTCHA, consent dialogs, and unfamiliar account-security prompts.
- Added configurable randomized delays between browser actions.
- Added progressive Liked Videos scrolling, visible-item extraction, canonical video ID parsing, and immediate per-video persistence.
- Added deterministic content fingerprints so unchanged videos are observed without being reclassified.
- Added browser adapters for video details, transcripts, and add-only playlist assignment.
- Added playlist assignment checks that treat an already-selected playlist as a successful idempotent result.

#### Classification and review

- Added validated YAML schemas and examples for categories and deterministic classification rules.
- Added priority-ordered keyword, regex, channel, and multi-category rule evaluation.
- Added optional OpenAI and local OpenAI-compatible classification providers. AI remains disabled by default.
- Added auditable AI run storage for prompt version, hashes, raw responses, parsed results, token usage, timing, cost fields, and errors.
- Added confidence-based automatic approval and human review routing.
- Added manual approval, rejection, and category assignment for uncertain or unclassified videos.
- Added initial manual-decision learning summaries without automatic rule mutation.

#### Planning, search, and interface

- Added durable playlist-add planning from approved category assignments.
- Added resumable playlist execution with stable action keys, attempt counters, status, timestamps, and error recording.
- Added title, description, and channel text search with approved-category filtering.
- Added deterministic local summaries sourced from descriptions or transcripts.
- Added an explicit semantic-search capability status that does not send local content to a provider.
- Added Streamlit pages for the dashboard, collection, categories, review queue, playlist plan, search, and sanitized settings.

#### Operations and documentation

- Added Windows PowerShell and cross-platform shell scripts for bootstrap, synchronization, and Streamlit startup.
- Added CLI commands for database initialization, manual browser login, synchronization, classification, planning, playlist execution, and local search.
- Added dry-run defaults for collection persistence, classification writes, plan persistence, and all YouTube playlist changes.
- Added architecture, browser automation, classification, database, privacy, troubleshooting, and roadmap documentation.
- Added a local dry-run Docker configuration. Authenticated interactive browser automation remains a host workflow.

#### Testing and verification

- Added unit tests for rules, duration parsing, fingerprints, incremental upserts, idempotent planning, search, and summaries.
- Added mocked browser URL parsing coverage.
- Added an Alembic integration test for every required table.
- Added CI checks for Ruff linting, Ruff formatting, strict mypy, and pytest with live YouTube tests excluded.
- Verified Ruff, strict mypy across 53 source files, nine non-live tests, Alembic schema drift, database initialization, CLI help, and private-runtime-file exclusion.

### Changed

- Replaced the starter README with complete installation, safety, configuration, operation, command, scope, and documentation guidance.
- Extended the starter Python `.gitignore` with application-specific private-data exclusions.

### Security

- Prohibited password storage, cookie exports, security-control bypasses, playlist deletion, Liked Videos removal, and playlist removal.
- Required explicit `--apply` authorization before any YouTube playlist write.
- Kept API keys in environment-based configuration and excluded private `.env` files from Git and Docker build contexts.

### Known limitations

- No authenticated live YouTube crawl or playlist write was run during the initial implementation.
- YouTube DOM selectors, transcript flows, and playlist dialogs require controlled live validation.
- Semantic search has an interface and privacy-safe unavailable status but no embedding implementation.
