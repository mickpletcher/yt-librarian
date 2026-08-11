# Completed upgrades

This tracked file is the permanent record of completed YouTube Knowledge Manager upgrades.

When an item from local-only `future-upgrades.md` is implemented, preserve its upgrade ID, remove it from the future ledger, and add it here with the completion date, actual scope, affected areas, and verification evidence. An upgrade must never appear in both files.

## UPG-016: Database integrity, backup, and restore commands

- Completed: 2026-08-11
- Status: Completed
- Scope:
  - Added read-only SQLite integrity, page-count, and free-page checks.
  - Added consistent verified backups through SQLite's backup API.
  - Added guarded restore with source verification, temporary restored-copy verification, explicit `--apply`, and an automatic pre-restore backup.
  - Added automatic verified pre-migration backups and stopped normal commands from migrating implicitly.
- Affected areas: Database operations service, CLI, locking, tests, CI, setup scripts, README, architecture, schema, privacy, troubleshooting, assessment, and changelog.
- Verification:
  - Backup and restore round trips pass against temporary SQLite databases on Windows.
  - CI exercises migration upgrade, schema drift, and downgrade.
  - Database operations are covered by the single-writer lock.

## UPG-015: Single-writer application lock

- Completed: 2026-08-11
- Status: Completed
- Scope:
  - Added an atomic lock adjacent to the configured SQLite database.
  - Recorded the owner token, process ID, operation, and start time.
  - Protected synchronization, enrichment, migrations, planning, playlist execution, backup, restore, browser login, and Streamlit mutation workflows.
  - Added explicit `unlock --force`; the app never removes a potentially active lock automatically.
- Affected areas: Operations package, CLI, Streamlit pages, scripts, ignores, tests, README, architecture, troubleshooting, assessment, and changelog.
- Verification:
  - Tests cover lock acquisition, competing writers, owner-safe release, and explicit stale-lock recovery.
  - Read-only database checks and searches remain available without taking the writer lock.

## UPG-013: Idempotent transcript enrichment

- Completed: 2026-08-11
- Status: Completed
- Scope:
  - Changed transcript persistence to upsert the unique video, language, and generation-type row.
  - Added attempt count, last-attempt time, next-retry time, and explicit pending, running, failed, skipped, and complete outcomes.
  - Preserved transcript text hashes and segments while successful retries clear stale errors.
- Affected areas: Transcript model and migration, enrichment service, repositories, CLI, tests, database documentation, README, assessment, and changelog.
- Verification:
  - Repeated successful enrichment updates one row rather than creating duplicates.
  - Failure tests record retry state and a later success clears the error.
  - Migration tests verify the retry columns.

## UPG-011: Complete mocked browser-flow tests

- Completed: 2026-08-11
- Status: Completed
- Scope:
  - Added mocked progressive scrolling and bounded hydration tests.
  - Added incomplete-crawl and interrupted-persistence coverage.
  - Added fail-closed CAPTCHA, consent, login, and security-prompt tests.
  - Added playlist ID matching, duplicate-name rejection, missing target, already-present, execution recovery, validation-only, and retry-state tests.
  - Kept live YouTube tests opt-in and excluded from normal CI.
- Affected areas: Browser, collection, planning, services, test fixtures, CI, README, assessment, and changelog.
- Verification:
  - The non-live suite passes with 70 tests and 77.54% coverage against a 75% floor.
  - Strict mypy and Ruff pass.
  - No real account is required by CI.

## UPG-028: Saved playlist inventory and safe optimization

- Completed: 2026-08-05
- Status: Completed
- Scope:
  - Added authenticated discovery of every saved playlist shown by YouTube, including Liked Videos and Watch Later.
  - Added reusable per-playlist video crawling with bounded hydration retries and existing fail-closed security checks.
  - Added normalized playlist and membership persistence with stable YouTube identities, active history, observed positions, and incremental upserts.
  - Added `sync-library` with read-only default, an optional playlist limit, resumable local writes, and safe isolation of normal per-playlist load failures.
  - Added local optimization for duplicate regular-playlist placement, empty and oversized playlists, uncategorized saved videos, and missing approved category additions.
  - Added `optimize-library`, the Streamlit Library Optimization page, collection scope selection, saved-playlist dashboard metrics, and planner suppression of known existing memberships.
  - Preserved the no-removal contract. Optimization creates local, add-only recommendations and never moves, merges, renames, creates, or deletes YouTube content.
- Affected areas: Database models and migration, repositories, browser selectors and collectors, synchronization, planning, services, CLI, Streamlit, tests, architecture, troubleshooting, README, assessment, changelog, and agent guidance.
- Verification:
  - Authenticated read-only discovery completed against the current YouTube saved-playlist layout.
  - One small saved playlist reconciled its displayed and collected available-video counts without local or YouTube writes.
  - Ruff formatting and lint passed, strict mypy passed across 58 source files, and 23 non-live tests passed.
  - Personal playlist names, video metadata, and library counts were excluded from tracked files.
- Remaining gate: Run and reconcile a complete read-only all-playlist crawl under local-only UPG-029 before relying on inventory completeness.

## UPG-027: Current Liked Videos layout and scalable extraction

- Completed: 2026-08-04
- Status: Completed
- Scope:
  - Added support for YouTube's current `yt-lockup-view-model` playlist layout while retaining the classic renderer.
  - Added watch, Shorts, and live URL parsing.
  - Replaced repeated per-element browser calls with one bulk extraction per visible batch.
  - Added resilient navigation and playlist hydration timeouts.
  - Added three bounded hydration attempts that stop immediately for login or security intervention.
  - Replaced the final raw locator timeout with an actionable playlist-load error.
  - Preserved security-prompt checks, randomized scroll delays, and read-only defaults.
- Affected areas: Browser selectors, Liked Videos collection, URL normalization, performance, tests, troubleshooting, and operator documentation.
- Verification:
  - A real authenticated read-only crawl completed with `created=0`, `changed=0`, and `dry_run=True`.
  - Personal library counts and video metadata were not added to tracked files.
  - The read-only crawl completed again after the bounded retry change.
  - Ruff passed, strict mypy passed across 54 source files, and 15 non-live tests passed.
- Remaining gate: Hidden unavailable entries and representative boundary samples still require reconciliation under UPG-009.

## UPG-026: Normal browser authentication and authenticated CDP attachment

- Completed: 2026-08-04
- Status: Completed
- Scope:
  - Changed manual login to start installed Chrome or Edge directly without Playwright or remote debugging.
  - Changed sync and playlist automation to start the same branded browser with the dedicated profile, then attach Playwright over an ephemeral loopback-only CDP endpoint.
  - Made Chrome the default browser channel and retained bundled Chromium for unauthenticated automation only.
  - Added clear failure guidance when the dedicated profile is already open.
  - Added tests and operator documentation for the browser command boundary.
- Affected areas: Browser authentication, automation session startup, configuration, tests, and operator documentation.
- Verification:
  - Normal Chrome displayed the authenticated Liked Videos playlist and account avatar with the dedicated profile.
  - A private-data-free headless Chrome smoke test connected over CDP, loaded a local data page, and closed successfully.
  - Ruff passed, strict mypy passed across 54 source files, and 15 non-live tests passed.
- Remaining gate: A read-only full Liked Videos crawl and count reconciliation are still required under UPG-009.

## UPG-008: Upgrade lifecycle and ledgers

- Completed: 2026-08-04
- Status: Completed
- Scope:
  - Added this tracked completion ledger.
  - Added local-only `future-upgrades.md` with project-specific priorities and acceptance criteria.
  - Added `/future-upgrades.md` to `.gitignore`.
  - Required shipped future items to be removed from the future ledger and added here with their original ID.
  - Added cross-file synchronization requirements to `AGENTS.md`, `README.md`, `CHANGELOG.md`, and `assessment.md`.
- Affected areas: Repository governance and project documentation.
- Verification:
  - `git check-ignore -v future-upgrades.md` identifies the root ignore rule.
  - `git status --short --ignored -- future-upgrades.md` reports `!! future-upgrades.md`.
  - README links to this file.

## UPG-007: Detailed operator README

- Completed: 2026-08-04
- Status: Completed
- Scope:
  - Expanded the README into a Windows-first setup and operations guide.
  - Documented bootstrap and manual installation.
  - Documented safe first-run collection, local persistence, classification, review, planning, and one-item playlist validation.
  - Documented all CLI commands, flags, settings, category and rule formats, AI providers, Streamlit pages, migrations, Docker, troubleshooting, development, privacy, and known limitations.
  - Clarified that only `apply-plan --apply` changes YouTube.
- Affected areas: Operator documentation and safety guidance.
- Verification:
  - All local README links resolve.
  - CLI help, settings, and scripts were inspected against the documented behavior.
  - Ruff, strict mypy, and all non-live tests passed after the change.

## UPG-006: Living assessment and changelog governance

- Completed: 2026-08-03
- Status: Completed
- Scope:
  - Added a deep project assessment with coverage, risk, readiness, priorities, and release gates.
  - Added a changelog covering the initial repository implementation and later changes.
  - Required `README.md`, `CHANGELOG.md`, and `assessment.md` to remain synchronized for every repository change.
  - Required future agents to read the assessment before changing the project.
- Affected areas: Repository governance and documentation.
- Verification:
  - Required files exist and are referenced by `AGENTS.md` and the README.
  - Repository validation remained green.

## UPG-005: Development, packaging, and validation baseline

- Completed: 2026-08-03
- Status: Completed
- Scope:
  - Added Python packaging, dependency locking, Ruff, strict mypy, pytest, and Alembic.
  - Added PowerShell and shell bootstrap and run scripts.
  - Added Docker and GitHub Actions configurations.
  - Added architecture, browser, classification, database, privacy, troubleshooting, and roadmap documentation.
  - Added private-data exclusions for Git and Docker contexts.
- Affected areas: Tooling, CI, installation, testing, and documentation.
- Verification:
  - `uv sync --all-extras` completed.
  - Ruff lint and format checks passed.
  - Strict mypy passed across 53 source files.
  - Nine non-live tests passed.
  - Alembic migration and schema-drift checks passed.

## UPG-004: Local search, Streamlit review, and playlist planning

- Completed: 2026-08-03
- Status: Completed
- Scope:
  - Added Streamlit pages for dashboard, collection, categories, review, playlist planning, search, and sanitized settings.
  - Added text search, approved-category filtering, and local description or transcript summaries.
  - Added durable playlist-add plans and resumable execution state.
  - Added stable action keys and already-present playlist handling.
- Affected areas: UI, search, planning, and browser action execution.
- Verification:
  - Search and planning tests passed.
  - Playlist actions remain add-only and require explicit apply mode.

## UPG-003: Deterministic and optional AI classification

- Completed: 2026-08-03
- Status: Completed
- Scope:
  - Added validated category and rule YAML formats.
  - Added priority-ordered keyword, regex, channel, and multi-category rule evaluation.
  - Added optional OpenAI and local OpenAI-compatible providers.
  - Added auditable classification runs and confidence-based human review.
  - Added manual decisions for low-confidence and unclassified videos.
- Affected areas: Classification, review, configuration, and persistence.
- Verification:
  - Rule and multi-category tests passed.
  - AI remains disabled by default.

## UPG-002: Safe incremental browser collection

- Completed: 2026-08-03
- Status: Completed
- Scope:
  - Added a dedicated persistent Playwright profile.
  - Added manual authentication and security-intervention stops.
  - Added centralized selectors, progressive Liked Videos scrolling, throttling, and immediate persistence.
  - Added content fingerprints so only new or changed videos return to classification.
  - Added browser adapters for details, transcripts, and add-only playlist assignment.
- Affected areas: Browser automation, collection, synchronization, and safety.
- Verification:
  - Pure parsing, duration, fingerprint, and incremental persistence tests passed.
  - Live authenticated collection remains a release gate and is not recorded as completed.

## UPG-001: Local-first application and database foundation

- Completed: 2026-08-03
- Status: Completed
- Scope:
  - Created the Python 3.12+ application package and CLI.
  - Added normalized SQLite and SQLAlchemy models for videos, transcripts, categories, assignments, classification runs and rules, synchronization runs, and browser actions.
  - Added repositories, services, structured logging, Pydantic Settings, and the initial Alembic migration.
  - Established dry-run and privacy-first defaults.
- Affected areas: Entire initial application foundation.
- Verification:
  - Database initialization and migration tests passed.
  - CLI command discovery passed.
  - Private runtime files were not Git candidates.
