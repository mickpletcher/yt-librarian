# Completed upgrades

This tracked file is the permanent record of completed YouTube Knowledge Manager upgrades.

When an item from local-only `future-upgrades.md` is implemented, preserve its upgrade ID, remove it from the future ledger, and add it here with the completion date, actual scope, affected areas, and verification evidence. An upgrade must never appear in both files.

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
