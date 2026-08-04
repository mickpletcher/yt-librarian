# Changelog

Every repository change is recorded in this file. Entries describe behavior, code, configuration, tests, documentation, and operational changes. Dates use `YYYY-MM-DD`.

## Unreleased

### Added

- Added `assessment.md` as the required pre-change project baseline, architecture assessment, requirement coverage matrix, verification record, risk register, and prioritized work list.
- Added this changelog and the requirement to record every delivered repository change.
- Added tracked `completed-upgrades.md` as the permanent ledger for shipped project upgrades and their verification evidence.
- Added local-only `future-upgrades.md` with prioritized, project-specific upgrade ideas and measurable acceptance criteria.

### Changed

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
