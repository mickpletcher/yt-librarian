# YouTube Knowledge Manager

YouTube Knowledge Manager is a local-first Python application for collecting, classifying, reviewing, searching, and organizing the videos in your YouTube Liked Videos playlist.

It uses Playwright with a dedicated authenticated browser profile. It does not use the YouTube Data API for bulk collection or playlist assignment. Video metadata, classifications, transcripts, action history, and review state are stored in a local SQLite database.

The application never asks for or stores your Google password. You sign in manually through Google's normal browser pages.

## Project status

Current version: `0.1.0`

Lifecycle: Alpha

The architecture, database, command-line interface, Streamlit interface, tests, migrations, and safety controls are implemented and locally verified. A full authenticated crawl and real playlist assignment have not been validated against this account yet. Treat the first live runs as controlled tests.

Read [assessment.md](assessment.md) before changing the project. It contains the current requirement coverage, architecture assessment, verification results, risks, release gates, and prioritized work. See [CHANGELOG.md](CHANGELOG.md) for every delivered repository change.

See [completed-upgrades.md](completed-upgrades.md) for the permanent record of shipped upgrades. The working backlog is stored in local-only `future-upgrades.md`, which is intentionally ignored by Git and must never be force-added.

## What the application does

- Opens YouTube using a dedicated persistent Chromium profile.
- Lets you authenticate manually without exposing credentials to the application.
- Progressively scrolls through the Liked Videos playlist.
- Extracts visible video IDs, titles, channels, thumbnails, durations, URLs, and playlist positions.
- Stores each discovered video immediately when write mode is enabled.
- Uses content fingerprints to detect new or changed videos.
- Classifies videos with deterministic YAML rules.
- Optionally classifies unmatched videos with OpenAI or a local OpenAI-compatible service.
- Allows a video to belong to multiple categories.
- Routes uncertain and unclassified videos to a Streamlit review queue.
- Creates durable, idempotent proposals for YouTube playlist additions.
- Adds approved videos to YouTube playlists only after an explicit apply command.
- Searches local titles, descriptions, and channel names.
- Filters search results by approved category.
- Produces simple local summaries from descriptions or transcripts.
- Records synchronization runs, classification evidence, action attempts, failures, and completion state.

## What the application does not do

- It does not remove videos from Liked Videos.
- It does not delete YouTube playlists.
- It does not remove videos from existing playlists.
- It does not create YouTube playlists automatically.
- It does not bypass CAPTCHA, login challenges, consent screens, rate limits, or account-security controls.
- It does not accept exported cookies or passwords.
- It does not perform a YouTube write during collection, classification, review, search, or planning.
- It does not provide semantic search yet.
- It is not ready for unattended playlist changes.

## Safety model

There are four different operation types. They are intentionally separate.

| Operation | Reads YouTube | Writes local SQLite | Writes a local action plan | Changes YouTube |
| --- | --- | --- | --- | --- |
| `ykm sync` | Yes | No | No | No |
| `ykm sync --write` | Yes | Yes | No | No |
| `ykm classify --write` | No | Yes | No | No |
| `ykm plan --write` | No | Yes | Yes | No |
| `ykm apply-plan` | No | No | No | No |
| `ykm apply-plan --apply` | Yes | Yes | Uses existing plan | Yes, add-only |

The only command that changes YouTube is:

```powershell
uv run ykm apply-plan --apply
```

Do not run it until you have inspected the local categories, review decisions, and playlist plan.

Browser operations use configurable randomized delays. The session stops when it detects CAPTCHA, login, consent, or known account-security prompts. Resolve those prompts manually with `browser-login`. Do not automate around them.

## Requirements

### Windows

- Windows 11 is the primary platform.
- Python 3.12 or newer.
- PowerShell 7 is recommended. Windows PowerShell also works for the supplied scripts.
- [uv](https://docs.astral.sh/uv/) for Python and dependency management.
- A graphical desktop session for manual YouTube authentication.
- Enough local storage for the SQLite database, browser profile, metadata, and optional transcripts.

Check the installed tools:

```powershell
py -0p
uv --version
git --version
```

The bootstrap process creates a Python 3.12 virtual environment through uv. It does not use the system Python 3.11 installation when Python 3.12 is available.

### macOS and Linux

Python 3.12+, uv, Git, and a graphical session are required. Shell scripts are included, but Windows is the currently verified platform.

## Fast Windows setup

Run all commands from the repository root:

```powershell
Set-Location 'C:\Users\mick0\OneDrive\Documents\Code & Dev\GitHub\yt-librarian'
.\scripts\bootstrap.ps1
```

The bootstrap script performs these steps:

1. Runs `uv sync --all-extras`.
2. Installs the Playwright Chromium browser.
3. Creates `.env` from `.env.example` if `.env` does not exist.
4. Creates `config/categories.yaml` from the category example if it does not exist.
5. Creates `config/rules.yaml` from the rule example if it does not exist.
6. Runs all Alembic database migrations.

The bootstrap script does not overwrite existing `.env`, `categories.yaml`, or `rules.yaml` files.

If script execution is blocked for the current PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\bootstrap.ps1
```

Do not change the machine-wide execution policy just to run this project.

## Manual setup

Use this when you want to run each setup step yourself.

```powershell
uv sync --all-extras
uv run playwright install chromium

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}

if (-not (Test-Path config\categories.yaml)) {
    Copy-Item config\categories.example.yaml config\categories.yaml
}

if (-not (Test-Path config\rules.yaml)) {
    Copy-Item config\rules.example.yaml config\rules.yaml
}

uv run alembic upgrade head
uv run ykm init-db
```

`alembic upgrade head` creates or upgrades the schema. `ykm init-db` also synchronizes categories from the configured YAML file.

## macOS and Linux setup

```bash
chmod +x scripts/*.sh
./scripts/bootstrap.sh
```

The shell bootstrap performs the same dependency, browser, configuration, and migration setup as the PowerShell script.

## First-run workflow

Use this sequence for the first controlled run.

### 1. Review local configuration

Open these private local files:

```text
.env
config/categories.yaml
config/rules.yaml
```

Confirm the database path, browser profile path, action delays, category names, rule category slugs, and YouTube playlist names.

The private files are ignored by Git. Do not force-add them.

### 2. Create the YouTube playlists manually

The application adds videos to existing playlists. It does not create playlists.

Create the desired playlists in YouTube. Make each `youtube_playlist_name` in `config/categories.yaml` exactly match the visible playlist name in YouTube.

Example:

```yaml
categories:
  - name: Software Engineering
    slug: software-engineering
    description: Programming, architecture, developer tools, and engineering practices.
    youtube_playlist_name: Knowledge - Software Engineering
```

The current browser executor locates playlists by exact visible name. A stored playlist ID is retained for planning and identity, but visible-name matching is still required during browser execution.

### 3. Authenticate the dedicated browser profile

```powershell
uv run ykm browser-login
```

This command:

1. Creates or opens the dedicated profile configured by `YKM_BROWSER_PROFILE_DIR`.
2. Opens the Liked Videos playlist.
3. Leaves authentication and security prompts under your control.
4. Waits for you to press Enter in PowerShell.
5. Closes the Playwright browser cleanly.

Sign in manually. Confirm the browser can display your Liked Videos playlist. Resolve any normal Google prompt yourself. Return to PowerShell and press Enter only when finished.

Do not point the application at your normal Chrome or Edge profile. Use the dedicated profile under `data/browser-profile`. Do not open that same profile in two browser processes at once.

### 4. Run a read-only collection preview

```powershell
uv run ykm sync
```

This opens the authenticated profile, reads the playlist, scrolls until the visible video count is stable, and reports how many videos it saw. It does not persist videos or classifications.

For the first real playlist, compare the reported count with YouTube. Also compare representative entries near the beginning, middle, and end of the playlist before trusting completeness.

If YouTube presents CAPTCHA, login, consent, or a security challenge, the run stops. Use `browser-login`, resolve it manually, close the browser, and rerun the preview.

### 5. Persist videos and classify them

```powershell
uv run ykm sync --write
```

This command does not modify YouTube. It:

1. Synchronizes local categories from YAML.
2. Crawls the Liked Videos playlist.
3. Stores every newly discovered video as it appears.
4. Updates metadata for changed fingerprints.
5. Leaves unchanged videos observed but not reclassified.
6. Runs deterministic rules against pending videos.
7. Uses the configured AI provider only when rules do not match and AI is enabled.
8. Stores assignments, review state, classification evidence, and synchronization counters.

If the crawl is interrupted, previously committed discoveries remain in SQLite. Rerun the same command after resolving the problem.

### 6. Start Streamlit and review results

```powershell
.\scripts\run_app.ps1
```

Equivalent command:

```powershell
uv run streamlit run src/youtube_knowledge_manager/ui/app.py
```

Streamlit normally opens `http://localhost:8501`.

Review categories and uncertain videos. Approve good proposals, reject bad proposals, and manually assign categories to unclassified videos.

### 7. Preview the playlist plan

```powershell
uv run ykm plan
```

This computes eligible playlist additions and reports counts. It rolls back the proposed action rows after the preview. It does not open a browser or modify YouTube.

### 8. Persist the playlist plan

```powershell
uv run ykm plan --write
```

This stores idempotent local browser-action rows for approved category assignments. It does not modify YouTube.

Open the Streamlit Playlist Plan page and inspect the video, target playlist, status, attempts, and errors.

### 9. Confirm the pending action count

```powershell
uv run ykm apply-plan
```

Without `--apply`, this only reports how many actions are pending. It does not open the browser and does not modify YouTube.

### 10. Test one real playlist addition

After the dry-run and plan have been inspected:

```powershell
uv run ykm apply-plan --apply --limit 1
```

Verify the result directly in YouTube. Confirm that rerunning the same action does not create a duplicate and that an already-selected playlist is treated as complete.

Only increase the limit after the one-item test succeeds:

```powershell
uv run ykm apply-plan --apply --limit 10
```

Keep batches small during alpha validation.

## Routine synchronization

For later runs:

```powershell
uv run ykm sync --write
.\scripts\run_app.ps1
uv run ykm plan
uv run ykm plan --write
uv run ykm apply-plan
```

Review the plan before deciding whether to run `apply-plan --apply`.

The crawler still scans the playlist to establish what is visible. The database fingerprint determines whether each existing video changed. Only new or changed videos return to pending classification.

The supplied sync wrapper accepts normal CLI arguments:

```powershell
.\scripts\run_sync.ps1
.\scripts\run_sync.ps1 --write
```

## Configuration

Settings are loaded from `.env` with the `YKM_` prefix. Environment variables override the defaults. Run commands from the repository root so relative paths resolve correctly.

### Environment settings

| Setting | Default | Purpose |
| --- | --- | --- |
| `YKM_DATABASE_URL` | `sqlite:///data/youtube_knowledge_manager.sqlite3` | SQLAlchemy URL for the local database. |
| `YKM_BROWSER_PROFILE_DIR` | `data/browser-profile` | Dedicated persistent authentication profile. |
| `YKM_BROWSER_CHANNEL` | `chromium` | Browser channel. Supported values are `chromium`, `chrome`, and `msedge`. |
| `YKM_HEADLESS` | `false` | Runs without a visible browser when true. Keep false for login and early validation. |
| `YKM_DRY_RUN` | `true` | Retained application safety setting. CLI and UI operations still require their explicit write controls. Do not treat this value as write authorization. |
| `YKM_ALLOW_PLAYLIST_REMOVALS` | `false` | Reserved safety setting. Playlist removal is not implemented even if changed. |
| `YKM_MIN_ACTION_DELAY_SECONDS` | `1.5` | Minimum randomized delay between browser actions. Minimum accepted value is 0.5. |
| `YKM_MAX_ACTION_DELAY_SECONDS` | `3.5` | Maximum randomized delay. It must not be less than the minimum. |
| `YKM_MAX_SCROLLS` | `500` | Maximum progressive-scroll iterations. Accepted range is 1 through 10,000. |
| `YKM_STABLE_SCROLL_LIMIT` | `4` | Consecutive unchanged collection rounds before stopping. Accepted range is 2 through 20. |
| `YKM_CATEGORIES_PATH` | `config/categories.yaml` | Local category configuration. |
| `YKM_RULES_PATH` | `config/rules.yaml` | Local deterministic rule configuration. |
| `YKM_REVIEW_CONFIDENCE_THRESHOLD` | `0.75` | Minimum confidence for automatic approval. Accepted range is 0 through 1. |
| `YKM_AI_PROVIDER` | `none` | Optional provider: `none`, `openai`, or `local`. |
| `YKM_AI_MODEL` | `gpt-5-mini` | Provider-specific model name. Confirm availability with the configured provider. |
| `YKM_AI_BASE_URL` | `http://localhost:11434/v1` | Base URL for a local OpenAI-compatible chat-completions service. |
| `YKM_AI_PROMPT_VERSION` | `v1` | Audit label stored with classification runs. |
| `YKM_LOG_LEVEL` | `INFO` | Structured console log level. |
| `OPENAI_API_KEY` | None | OpenAI client credential. Set only when the OpenAI provider is enabled. |

Example `.env`:

```dotenv
YKM_DATABASE_URL=sqlite:///data/youtube_knowledge_manager.sqlite3
YKM_BROWSER_PROFILE_DIR=data/browser-profile
YKM_BROWSER_CHANNEL=chromium
YKM_HEADLESS=false
YKM_DRY_RUN=true
YKM_MIN_ACTION_DELAY_SECONDS=1.5
YKM_MAX_ACTION_DELAY_SECONDS=3.5
YKM_MAX_SCROLLS=500
YKM_STABLE_SCROLL_LIMIT=4
YKM_CATEGORIES_PATH=config/categories.yaml
YKM_RULES_PATH=config/rules.yaml
YKM_REVIEW_CONFIDENCE_THRESHOLD=0.75
YKM_AI_PROVIDER=none
YKM_LOG_LEVEL=INFO
```

### Category configuration

Each category supports these fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `name` | Yes | Human-readable local category name. |
| `slug` | Yes | Stable unique identifier used by rules and search filters. |
| `description` | No | Category guidance for people and AI providers. |
| `parent_slug` | No | Slug of an existing parent category. Parent categories are synchronized first. |
| `youtube_playlist_name` | No | Exact visible YouTube playlist name used by browser execution. |
| `youtube_playlist_id` | No | Known YouTube playlist identifier retained with the local mapping. |
| `enabled` | No | Defaults to true. Disabled categories are excluded from normal use. |
| `system_managed` | No | Marks categories managed by the application or supplied configuration. |

Example hierarchy:

```yaml
categories:
  - name: Technology
    slug: technology
    description: Parent category for technical material.
    youtube_playlist_name: Knowledge - Technology

  - name: PowerShell
    slug: powershell
    parent_slug: technology
    description: PowerShell scripting and automation.
    youtube_playlist_name: Knowledge - PowerShell
```

Category slugs should remain stable after videos have been classified. Renaming a slug is not currently handled as a migration.

### Rule configuration

Rules are evaluated from highest priority to lowest priority. A rule can assign one video to multiple categories.

Supported fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `name` | Yes | Unique audit identifier for the rule. |
| `priority` | No | Higher values run first. Defaults to 0. |
| `enabled` | No | Defaults to true. |
| `any_keywords` | No | At least one keyword must appear in title, description, or transcript. |
| `all_keywords` | No | Every listed keyword must appear. |
| `regex_patterns` | No | At least one regular expression must match. |
| `channels` | No | Channel name must exactly match after case normalization. |
| `categories` | Yes | One or more category slugs to assign. The first result is primary. |
| `confidence` | Yes | Value from 0 through 1. |

When a rule uses more than one match group, every configured group must pass. For example, a rule with `any_keywords` and `channels` requires both a keyword match and a channel match.

Example:

```yaml
rules:
  - name: powershell-endpoint-management
    priority: 100
    enabled: true
    any_keywords: [powershell, intune, configmgr, sccm]
    regex_patterns: ["\\bentra( id)?\\b"]
    categories: [powershell, endpoint-management]
    confidence: 0.95
```

Every slug in `categories` must exist in the category YAML file.

### OpenAI classification

AI classification runs only when deterministic rules return no decision.

Set the provider and model in private configuration:

```dotenv
YKM_AI_PROVIDER=openai
YKM_AI_MODEL=gpt-5-mini
```

Set the API key for the current PowerShell session:

```powershell
$env:OPENAI_API_KEY = 'your-private-key'
uv run ykm classify --write
Remove-Item Env:OPENAI_API_KEY
```

In the current version, `OPENAI_API_KEY` must be present in the process environment used to start `ykm`. The commented line in `.env.example` is a reminder, but Pydantic does not export that value into the process environment for the OpenAI client. Never commit the key.

Enabling a remote AI provider can send the video's title, description, channel, transcript text, and allowed category descriptions to that provider. Review [docs/privacy-and-security.md](docs/privacy-and-security.md) first.

### Local AI classification

The local provider expects an OpenAI-compatible `/chat/completions` endpoint.

```dotenv
YKM_AI_PROVIDER=local
YKM_AI_MODEL=your-local-model
YKM_AI_BASE_URL=http://localhost:11434/v1
```

Confirm the endpoint and model independently before enabling local classification. Provider errors are recorded with the classification run.

## Command reference

### Initialize or migrate the database

```powershell
uv run ykm init-db
```

Creates or migrates the database and synchronizes categories. Safe to rerun.

### Open the manual login browser

```powershell
uv run ykm browser-login
```

Uses the dedicated profile. Press Enter in the terminal after authentication is complete.

### Preview collection

```powershell
uv run ykm sync
```

Reads YouTube and reports the visible count. Does not persist discoveries.

### Persist collection and run classification

```powershell
uv run ykm sync --write
```

Writes only to local SQLite. Does not modify YouTube.

### Classify pending local videos

```powershell
uv run ykm classify
uv run ykm classify --limit 500
uv run ykm classify --write --limit 500
```

Without `--write`, the command processes pending records in preview mode and reports the count but does not persist assignments. The allowed limit is 1 through 10,000. Default: 100.

### Preview and persist a playlist plan

```powershell
uv run ykm plan
uv run ykm plan --write
```

Both are local operations. The first rolls back proposed actions. The second persists them.

### Inspect and apply pending playlist actions

```powershell
uv run ykm apply-plan
uv run ykm apply-plan --apply --limit 1
uv run ykm apply-plan --apply --limit 10
```

Without `--apply`, only the pending count is printed. With `--apply`, the application opens YouTube and performs add-only playlist assignments. The allowed limit is 1 through 1,000. Default: 100.

### Search the local database

```powershell
uv run ykm search powershell
uv run ykm search 'solar design'
uv run ykm search automation --category ai-automation
```

Search covers title, description, and channel name. The category option accepts an enabled category slug and filters to approved assignments.

### Display help

```powershell
uv run ykm --help
uv run ykm sync --help
uv run ykm apply-plan --help
```

## Streamlit interface

Start the application:

```powershell
.\scripts\run_app.ps1
```

### Dashboard

Shows total videos, review items, pending playlist actions, and the last synchronization status.

### Collection

Starts a browser collection scan. The `Persist discovered and changed videos` checkbox controls local database writes. This page runs collection only. For the full collect-and-classify workflow, use `ykm sync --write` from PowerShell.

### Categories

Displays enabled category names, slugs, parent relationships, playlist mappings, and enabled state. Edit category YAML outside Streamlit, then rerun `ykm init-db` to synchronize changes.

### Review Queue

Shows low-confidence proposed assignments. You can approve or reject each proposal. Unclassified videos can be assigned manually to an enabled category.

### Playlist Plan

Generates and displays local playlist proposals. The persist checkbox controls whether new action rows are committed. This page does not execute YouTube changes. Use the CLI apply command after review.

### Search

Searches titles, descriptions, and channels. Results can be filtered by category and include a local description or transcript summary when available.

### Settings

Displays non-secret effective settings. Secrets are intentionally omitted. Edit `.env` and restart Streamlit to apply changes because settings are cached for the application process.

## Local data locations

| Data | Default location | Git status |
| --- | --- | --- |
| SQLite database | `data/youtube_knowledge_manager.sqlite3` | Ignored |
| Browser authentication profile | `data/browser-profile/` | Ignored |
| Private environment settings | `.env` | Ignored |
| Private categories | `config/categories.yaml` | Ignored |
| Private rules | `config/rules.yaml` | Ignored |
| Example categories | `config/categories.example.yaml` | Tracked |
| Example rules | `config/rules.example.yaml` | Tracked |
| Alembic migrations | `migrations/` | Tracked |
| Tests | `tests/` | Tracked |

The browser profile contains authenticated session material. Treat it as sensitive. Do not copy it to Git, cloud-shared examples, issue attachments, or diagnostic bundles.

The SQLite database can contain personal viewing metadata, transcripts, classifications, AI responses, and playlist plans. Treat it as private.

## Database migrations

Apply all migrations:

```powershell
uv run alembic upgrade head
```

Display the current revision:

```powershell
uv run alembic current
```

Display migration history:

```powershell
uv run alembic history
```

Back up the private SQLite database before applying future migrations. A first-class backup command is planned but not implemented.

## Troubleshooting

### `uv` is not recognized

Install uv using its official instructions, open a new PowerShell session, and confirm:

```powershell
uv --version
```

### PowerShell blocks the bootstrap script

Use a process-scoped policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\bootstrap.ps1
```

### Playwright reports that the browser executable is missing

```powershell
uv run playwright install chromium
```

### The profile is already in use

Close every browser window created by `ykm browser-login`, synchronization, or playlist execution. The dedicated profile cannot be used by two Chromium processes simultaneously.

Do not delete the profile unless you intend to lose its authenticated session.

### YouTube asks for login, consent, CAPTCHA, or account verification

The application should stop. Run:

```powershell
uv run ykm browser-login
```

Resolve the prompt manually. Close the browser through the terminal workflow, then retry the previous command. Do not add code that clicks through or bypasses the security control.

### The crawler reports zero videos

1. Run `browser-login`.
2. Confirm the dedicated profile can open `https://www.youtube.com/playlist?list=LL`.
3. Confirm the Liked Videos list contains visible items.
4. Keep `YKM_HEADLESS=false`.
5. Run `ykm sync` again.
6. If the page is visible but nothing is collected, YouTube may have changed its DOM. Review centralized selectors in `src/youtube_knowledge_manager/browser/selectors.py`.

Do not commit screenshots or page captures containing personal data. Create sanitized fixtures for regression tests.

### The reported count is too low

Increase `YKM_MAX_SCROLLS` cautiously or increase `YKM_STABLE_SCROLL_LIMIT` in `.env`. Keep action delays conservative. Verify the end of the playlist manually. A low count can indicate virtualized scrolling or a selector change.

### SQLite reports that the database is locked

Close Streamlit and other `ykm` processes. Run only one synchronization or playlist executor at a time. SQLite has a busy timeout, but the application does not yet provide a single-writer lock.

### A category is missing

Confirm it exists and is enabled in `config/categories.yaml`, then run:

```powershell
uv run ykm init-db
```

### A rule does not classify a video

Check that:

- The rule is enabled.
- The category slugs exist.
- Confidence is between 0 and 1.
- Every configured match group passes.
- The video is pending classification.

Run:

```powershell
uv run ykm classify --write --limit 100
```

Changing a rule does not automatically reclassify videos already marked complete.

### A playlist cannot be found

Confirm the YouTube playlist already exists and `youtube_playlist_name` exactly matches its visible name. Playlist execution currently resolves the visible name, not only the stored ID.

### An action failed

Open the Streamlit Playlist Plan page and inspect its error. Failed actions remain eligible for retry. Resolve the underlying browser, authentication, or playlist-name issue, then apply a small batch.

### Resetting local data

Do not delete the entire `data` directory or browser profile as a general troubleshooting step.

To start a new database while preserving authentication:

1. Stop Streamlit and all CLI processes.
2. Back up `data/youtube_knowledge_manager.sqlite3` outside the repository.
3. Remove only that exact database file.
4. Run `uv run alembic upgrade head`.
5. Run `uv run ykm init-db`.

This loses local video, classification, review, synchronization, and action history. It does not modify YouTube.

See [docs/troubleshooting.md](docs/troubleshooting.md) for the shorter operational reference.

## Docker

Docker is intended for the local Streamlit UI and database inspection. Interactive authenticated browser automation is recommended on the Windows host.

Initialize the mounted SQLite database:

```powershell
docker compose build
docker compose run --rm app ykm init-db
docker compose up
```

Open `http://localhost:8501`.

The Compose service mounts `data/` for persistence and `config/` read-only. It forces headless and dry-run settings. Do not use this container workflow for the first authenticated browser session.

## Development and verification

Install all development and optional dependencies:

```powershell
uv sync --all-extras
```

Run the complete normal validation set:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -m "not live_youtube"
```

Format and safely fix lint issues:

```powershell
uv run ruff format .
uv run ruff check --fix .
```

Normal tests mock or isolate YouTube interactions. Live-account tests must use the `live_youtube` marker and must never run automatically in CI.

Useful Make targets on systems with Make:

```text
make install
make browser
make migrate
make lint
make typecheck
make test
make app
make sync
```

## Privacy checklist before staging

Run:

```powershell
git status --short
```

Confirm none of these are staged or untracked Git candidates:

- `.env`
- `data/*.sqlite3`
- `data/browser-profile/`
- `config/categories.yaml`
- `config/rules.yaml`
- Cookie or browser storage exports
- Transcripts
- Logs containing personal metadata
- Screenshots or HTML captures from the authenticated account

Only sanitized examples, fixtures, templates, migrations, and source code belong in Git.

## Known limitations

- Live YouTube selectors and playlist dialogs have not completed controlled validation.
- Unavailable playlist entries without a usable video ID may not be stored.
- Transcript extraction is best-effort and is not yet safely idempotent across retries.
- AI retries, timeouts, cost calculation, and spending limits are incomplete.
- Text search uses SQL `LIKE` rather than SQLite FTS5.
- Semantic embeddings and vector search are not implemented.
- Streamlit does not provide robust progress, cancellation, or bulk review controls.
- Concurrent writers are not protected by a dedicated application lock.
- Database backup and restore commands are not implemented.

See [assessment.md](assessment.md) for risk severity, prioritized work, and production release gates.

## Upgrade tracking

The project uses two upgrade ledgers:

- [completed-upgrades.md](completed-upgrades.md) is tracked in Git. It records shipped upgrades, completion dates, scope, affected areas, and verification evidence.
- `future-upgrades.md` is a local-only working backlog. The root file is ignored by Git. It contains upgrade ideas, priorities, risks, and acceptance criteria that may include local planning context.

When a future upgrade is implemented:

1. Keep its existing upgrade ID.
2. Implement and verify the complete acceptance criteria.
3. Remove the full item from local `future-upgrades.md`.
4. Add it to `completed-upgrades.md` with the completion date, actual shipped scope, affected files, and verification results.
5. Update `CHANGELOG.md`, this README, and `assessment.md` in the same change set.
6. Confirm the item does not appear in both future and completed ledgers.
7. Confirm `future-upgrades.md` remains ignored before staging.

Check the local-only status:

```powershell
git check-ignore -v future-upgrades.md
git status --short --ignored -- future-upgrades.md
```

The expected status marker is `!!`, meaning Git ignores the file.

## Documentation

- [Project assessment](assessment.md)
- [Changelog](CHANGELOG.md)
- [Completed upgrades](completed-upgrades.md)
- [Architecture](docs/architecture.md)
- [Browser automation](docs/browser-automation.md)
- [Classification](docs/classification.md)
- [Database schema](docs/database-schema.md)
- [Privacy and security](docs/privacy-and-security.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Roadmap](docs/roadmap.md)

## Change control

For every repository change:

1. Read `assessment.md` before editing.
2. Preserve privacy, dry-run defaults, add-only playlist behavior, and manual security intervention.
3. Implement and test the scoped change.
4. Record every delivered change in `CHANGELOG.md`.
5. Update this README when setup, commands, behavior, scope, status, or usage changes.
6. Update `assessment.md` when evidence, risk, readiness, coverage, or priorities change.
7. If a local future upgrade shipped, move it into `completed-upgrades.md` and remove it from `future-upgrades.md`.
8. Confirm private runtime files and `future-upgrades.md` remain excluded before staging.

Changes remain local until explicitly committed and pushed.
