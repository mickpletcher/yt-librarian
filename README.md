# YouTube Knowledge Manager

YouTube Knowledge Manager is a local-first Python application for collecting, classifying, reviewing, searching, and organizing videos from Liked Videos and every saved YouTube playlist.

It starts normal Google Chrome or Microsoft Edge with a dedicated authenticated profile, then attaches Playwright through a loopback-only debugging connection for automation. It does not use the YouTube Data API for bulk collection or playlist assignment. Video metadata, classifications, transcripts, action history, and review state are stored in a local SQLite database.

The application never asks for or stores your Google password. You sign in manually through Google's normal browser pages.

## Project status

Current version: `0.1.0`

Lifecycle: Production candidate

The architecture, database, command-line interface, Streamlit interface, migrations, operations, and safety controls are implemented and locally verified. The automated suite enforces a 75% coverage floor, security lint, dependency auditing, migration round trips, and private-file exclusions. A complete authenticated read-only saved-library crawl has run. Some playlist count mismatches, intermittent partial library discovery, a repeatable full local import, and one controlled add-only playlist action remain account-specific production gates.

Read [assessment.md](assessment.md) before changing the project. It contains the current requirement coverage, architecture assessment, verification results, risks, release gates, and prioritized work. See [CHANGELOG.md](CHANGELOG.md) for every delivered repository change.

See [completed-upgrades.md](completed-upgrades.md) for the permanent record of shipped upgrades. The working backlog is stored in local-only `future-upgrades.md`, which is intentionally ignored by Git and must never be force-added.

## What the application does

- Opens YouTube using a dedicated persistent Chrome or Edge profile.
- Lets you authenticate manually without exposing credentials to the application.
- Progressively scrolls through the Liked Videos playlist.
- Discovers every saved YouTube playlist, including Liked Videos and Watch Later.
- Crawls each discovered playlist and stores its current video memberships and positions.
- Preserves membership history by marking missing observations inactive instead of deleting them.
- Extracts visible video IDs, titles, channels, thumbnails, durations, URLs, and playlist positions.
- Stores each discovered video immediately when write mode is enabled.
- Uses content fingerprints to detect new or changed videos.
- Classifies videos with deterministic YAML rules.
- Optionally classifies unmatched videos with OpenAI or a local OpenAI-compatible service.
- Allows a video to belong to multiple categories.
- Routes uncertain and unclassified videos to a Streamlit review queue.
- Creates durable, idempotent proposals for YouTube playlist additions.
- Reports duplicate placement across regular playlists, empty and oversized playlists, uncategorized saved videos, and approved category additions that are still missing.
- Skips add proposals when the video is already known to be in the target playlist.
- Adds approved videos to YouTube playlists only after an explicit apply command.
- Searches local titles, descriptions, and channel names.
- Filters search results by approved category.
- Produces simple local summaries from descriptions or transcripts.
- Records synchronization runs, classification evidence, action attempts, failures, and completion state.
- Rejects incomplete playlist crawls for membership deactivation.
- Enriches metadata and transcripts with durable retry state.
- Prevents concurrent writers with an explicit application lock.
- Verifies SQLite integrity, backup, and restore operations.
- Produces a counts-only private-data inventory.

## What the application does not do

- It does not remove videos from Liked Videos.
- It does not delete YouTube playlists.
- It does not remove videos from existing playlists.
- It does not create YouTube playlists automatically.
- It does not rename, merge, reorder, or move playlists or videos.
- It does not automatically act on optimization findings.
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
| `ykm sync-library` | Yes | No | No | No |
| `ykm sync-library --write` | Yes | Yes | No | No |
| `ykm optimize-library` | No | No | No | No |
| `ykm optimize-library --write-plan` | No | Yes | Yes | No |
| `ykm classify --write` | No | Yes | No | No |
| `ykm enrich` | No | No | No | No |
| `ykm enrich --write` | Yes | Yes | No | No |
| `ykm plan --write` | No | Yes | Yes | No |
| `ykm apply-plan` | No | No | No | No |
| `ykm apply-plan --validate` | Yes | No | Uses existing plan | No |
| `ykm apply-plan --apply` | Yes | Yes | Uses existing plan | Yes, add-only |

The only command that changes YouTube is:

```powershell
uv run ykm apply-plan --apply
```

Do not run it until you have inspected the local categories, review decisions, and playlist plan.

Browser operations use configurable randomized delays. The session stops when it detects CAPTCHA, login, consent, or known account-security prompts. Resolve those prompts manually with `browser-login`. Do not automate around them.

YouTube calls its folders playlists. In this documentation, saved playlist library means every playlist shown at `https://www.youtube.com/feed/playlists`, plus the system playlists YouTube exposes there.

## Requirements

### Windows

- Windows 11 is the primary platform.
- Python 3.12 or newer.
- PowerShell 7 is recommended. Windows PowerShell also works for the supplied scripts.
- [uv](https://docs.astral.sh/uv/) for Python and dependency management.
- Google Chrome or Microsoft Edge. Chrome is the default browser channel.
- A graphical desktop session for manual YouTube authentication.
- Enough local storage for the SQLite database, browser profile, metadata, and optional transcripts.

Check the installed tools:

```powershell
py -0p
uv --version
git --version
```

The bootstrap process creates a Python 3.12 virtual environment through uv. On Windows it stores that environment under `%LOCALAPPDATA%\yt-librarian\.venv` with copy mode. This avoids OneDrive read-only reparse points inside repository-local environments.

### macOS and Linux

Python 3.12+, uv, Git, and a graphical session are required. Shell scripts are included, but Windows is the currently verified platform.

## Fast Windows setup

Run all commands from the repository root:

```powershell
Set-Location 'C:\Users\mick0\OneDrive\Documents\Code & Dev\GitHub\yt-librarian'
.\scripts\bootstrap.ps1
```

The bootstrap script performs these steps:

1. Selects `%LOCALAPPDATA%\yt-librarian\.venv` and runs `uv sync --all-extras` in copy mode.
2. Installs the Playwright Chromium browser.
3. Creates `.env` from `.env.example` if `.env` does not exist.
4. Creates `config/categories.yaml` from the category example if it does not exist.
5. Creates `config/rules.yaml` from the rule example if it does not exist.
6. Runs `ykm init-db`, which applies migrations under the application lock and synchronizes categories.

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
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:LOCALAPPDATA 'yt-librarian\.venv'
$env:UV_LINK_MODE = 'copy'
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

uv run ykm init-db
```

`ykm init-db` creates or upgrades the schema and synchronizes categories. If an existing database is behind the current migration head, it first creates and verifies a SQLite backup.

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

When `youtube_playlist_id` is configured, the Save dialog must expose that exact ID or execution fails closed. When no ID is configured, the executor requires exactly one exact visible-name match and rejects ambiguous duplicates.

### 3. Authenticate the dedicated browser profile

```powershell
uv run ykm browser-login
```

This command:

1. Creates or opens the dedicated profile configured by `YKM_BROWSER_PROFILE_DIR`.
2. Starts the installed Chrome or Edge application directly, without Playwright automation or a debugging connection.
3. Opens the Liked Videos playlist.
4. Leaves authentication and security prompts under your control.
5. Waits for you to close the dedicated browser completely and press Enter in PowerShell.

Sign in manually. Confirm the browser can display your Liked Videos playlist and account avatar. Resolve any normal Google prompt yourself. Use the browser menu to exit that dedicated browser completely, then return to PowerShell and press Enter.

Do not point the application at your normal Chrome or Edge profile. Use the dedicated profile under `data/browser-profile`. Do not open that same profile in two browser processes at once.

### 4. Run a read-only collection preview

```powershell
uv run ykm sync
```

This starts the same installed browser with the same authenticated profile. It enables a random loopback-only debugging port, attaches Playwright after the browser starts, reads the playlist, scrolls until the visible video count is stable, and reports how many videos it saw. It does not persist videos or classifications. The debugging port is not exposed to the network.

YouTube sometimes commits the playlist route before its item models hydrate. The collector makes up to three bounded load attempts. It checks for login and security intervention before each retry and stops immediately if either appears.

For the first real playlist, compare the reported count with YouTube. Also compare representative entries near the beginning, middle, and end of the playlist before trusting completeness.

The collector supports YouTube's classic `ytd-playlist-video-renderer`, current `yt-lockup-view-model`, and `yt-continuation-item-view-model` continuation layouts. It recognizes normal watch URLs, Shorts, and live-video URLs. Individual playlist crawls reject recommendation links whose `list` parameter does not identify the current playlist. Each visible batch is extracted in one browser call so large playlists do not repeatedly reparse every loaded item.

YouTube's playlist header can include unavailable videos even when the page says those videos are hidden. `ykm sync` counts only visible entries with a usable video ID. Record and investigate any difference before treating the crawl as fully reconciled.

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
uv run ykm apply-plan --validate --limit 1
uv run ykm apply-plan --apply --limit 1
```

The validation command opens and inspects the Save dialog without selecting anything or changing action state. Verify its target first. Then run the explicit apply command, verify the result directly in YouTube, and confirm that rerunning the same action does not create a duplicate. An already-selected target is recorded as successful.

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

## Saved playlist inventory and optimization

Use this workflow to inventory every saved YouTube playlist. It is separate from `ykm sync`, which only scans Liked Videos.

Start with a small read-only preview:

```powershell
uv run ykm sync-library --limit-playlists 3
```

This discovers the full saved playlist list but crawls only the selected number of playlists. Limited runs prioritize small regular playlists with known counts, which avoids starting validation with Liked Videos or Watch Later. It writes nothing locally and changes nothing on YouTube.

Run the complete read-only preview after the small test succeeds:

```powershell
uv run ykm sync-library
```

Record the exact discovered playlist count from the credible preview. Require that same count before a full local write:

```powershell
uv run alembic upgrade head
uv run ykm sync-library --write --expect-playlists 85
```

Replace `85` with the count from your own immediately preceding preview. An unrestricted write refuses to run without `--expect-playlists`. If discovery returns a different count, it stops before opening any individual playlist. This protects against YouTube intermittently exposing only a partial Playlists page while still appearing stable.

Write mode stores playlists, videos, active memberships, positions, observed timestamps, and reported playlist counts in SQLite. Each video is committed as it is observed so a later failure does not discard earlier work. A playlist that cannot load or reconcile its displayed count is reported and skipped. Login, CAPTCHA, consent, and security prompts stop the entire run. Memberships are marked inactive only after that playlist finishes successfully, which avoids false removals after an incomplete crawl. Abandoned synchronization runs are marked failed when the next write starts.

Analyze the stored inventory:

```powershell
uv run ykm optimize-library
uv run ykm optimize-library --oversized-threshold 300
```

The report is local and read only. It shows:

- Saved playlist count and system playlist count.
- Empty regular playlists.
- Regular playlists above the selected size threshold.
- Active playlist memberships and unique saved videos.
- Videos present in more than one regular playlist. Liked Videos and Watch Later are excluded from this duplicate calculation.
- Saved videos with no active regular playlist membership.
- Approved category assignments whose configured target playlist does not already contain the video.

Store only the add recommendations as the normal local playlist plan:

```powershell
uv run ykm optimize-library --write-plan
```

This does not change YouTube. Review the plan in Streamlit. `ykm apply-plan --apply` remains the only YouTube write command, and it remains add only. The optimizer never removes, moves, merges, renames, creates, or deletes anything on YouTube.

Run the workflow again when playlists change. Playlist identity is based on YouTube playlist ID, so a rename updates the local name without creating a duplicate playlist. Video identity is based on YouTube video ID. Repeated imports update observations and do not create duplicate memberships.

## Configuration

Settings are loaded from `.env` with the `YKM_` prefix. Environment variables override the defaults. Run commands from the repository root so relative paths resolve correctly.

### Environment settings

| Setting | Default | Purpose |
| --- | --- | --- |
| `YKM_DATABASE_URL` | `sqlite:///data/youtube_knowledge_manager.sqlite3` | SQLAlchemy URL for the local database. |
| `YKM_BROWSER_PROFILE_DIR` | `data/browser-profile` | Dedicated persistent authentication profile. |
| `YKM_BROWSER_CHANNEL` | `chrome` | Browser channel. Use `chrome` or `msedge` for manual Google sign-in. `chromium` remains available for unauthenticated automation only. |
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
| `YKM_AI_TIMEOUT_SECONDS` | `60` | Per-request timeout. Accepted range is 5 through 300 seconds. |
| `YKM_AI_MAX_RETRIES` | `2` | Bounded provider retries. Accepted range is 0 through 5. |
| `YKM_AI_DAILY_TOKEN_LIMIT` | `100000` | Stops new AI calls when today's recorded usage reaches the limit. Set 0 to disable AI calls. |
| `YKM_AI_INPUT_COST_PER_MILLION` | `0` | Local input-token price used for estimated cost. |
| `YKM_AI_OUTPUT_COST_PER_MILLION` | `0` | Local output-token price used for estimated cost. |
| `YKM_LOG_LEVEL` | `INFO` | Structured console log level. |
| `OPENAI_API_KEY` | None | OpenAI client credential. Set only when the OpenAI provider is enabled. |

Example `.env`:

```dotenv
YKM_DATABASE_URL=sqlite:///data/youtube_knowledge_manager.sqlite3
YKM_BROWSER_PROFILE_DIR=data/browser-profile
YKM_BROWSER_CHANNEL=chrome
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
YKM_AI_TIMEOUT_SECONDS=60
YKM_AI_MAX_RETRIES=2
YKM_AI_DAILY_TOKEN_LIMIT=100000
YKM_AI_INPUT_COST_PER_MILLION=0
YKM_AI_OUTPUT_COST_PER_MILLION=0
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

Starts normal Chrome or Edge with the dedicated profile and no automation connection. Confirm the account is visible, exit that browser completely, then press Enter in the terminal.

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

### Preview or persist every saved playlist

```powershell
uv run ykm sync-library
uv run ykm sync-library --limit-playlists 3
uv run ykm sync-library --write --expect-playlists 85
```

Without `--write`, the command discovers and crawls saved playlists without database mutation. `--limit-playlists` accepts a positive count and is intended for controlled validation. A full `--write` requires `--expect-playlists` to match the exact discovery result before playlist processing starts. Limited writes remain available for deliberate diagnostics. Write mode synchronizes configured categories, stores the playlist inventory and memberships, then classifies pending videos. It never changes YouTube.

### Analyze and plan library optimization

```powershell
uv run ykm optimize-library
uv run ykm optimize-library --oversized-threshold 300
uv run ykm optimize-library --write-plan
```

The default report is read only. `--oversized-threshold` must be positive and defaults to 500. `--write-plan` persists only missing approved category additions. It does not execute them and never creates removal actions.

### Classify pending local videos

```powershell
uv run ykm classify
uv run ykm classify --limit 500
uv run ykm classify --write --limit 500
```

Without `--write`, the command processes pending records with deterministic rules only and reports the count without persisting assignments or calling an AI provider. AI classification runs only with `--write`, so token use can be recorded and enforced against the daily ceiling. The allowed limit is 1 through 10,000. Default: 100.

### Enrich metadata and transcripts

```powershell
uv run ykm enrich --limit 100
uv run ykm enrich --write --limit 100
uv run ykm enrich --write --no-transcripts --limit 100
```

Preview mode reports eligible records without opening a browser. Write mode stores per-video success or failure state, attempt count, last attempt time, and retry eligibility. Completed transcript records are not duplicated on rerun.

### Preview and persist a playlist plan

```powershell
uv run ykm plan
uv run ykm plan --write
```

Both are local operations. The first rolls back proposed actions. The second persists them.

### Inspect and apply pending playlist actions

```powershell
uv run ykm apply-plan
uv run ykm apply-plan --validate --limit 1
uv run ykm apply-plan --apply --limit 1
uv run ykm apply-plan --apply --limit 10
```

Without `--apply` or `--validate`, only the pending count is printed. `--validate` opens dialogs and verifies target resolution without selecting a playlist or changing action state. `--apply` performs add-only playlist assignments. The flags are mutually exclusive. The allowed limit is 1 through 1,000. Default: 100.

### Check, back up, and restore SQLite

```powershell
uv run ykm db-check
uv run ykm db-backup
uv run ykm db-backup --destination D:\PrivateBackups\ykm.sqlite3
uv run ykm db-restore D:\PrivateBackups\ykm.sqlite3 --apply
```

Backup and restore use SQLite's supported backup API and verify integrity. Restore requires `--apply` and creates a verified pre-restore backup when an active database exists.

### Report a privacy-safe data inventory

```powershell
uv run ykm data-inventory
uv run ykm data-inventory --output data\inventory.json
```

The JSON contains a schema version and table counts only. It excludes names, URLs, paths, transcript content, AI responses, credentials, and browser state.

### Remove a stale application lock

```powershell
uv run ykm unlock --force
```

Use this only after confirming the process recorded in the lock file is no longer running. Locks are never removed automatically.

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
uv run ykm sync-library --help
uv run ykm optimize-library --help
uv run ykm apply-plan --help
```

## Streamlit interface

Start the application:

```powershell
.\scripts\run_app.ps1
```

### Dashboard

Shows total videos, saved playlists, review items, pending playlist actions, and the last synchronization status.

### Collection

Starts either a Liked Videos scan or an all saved playlists scan. Select the scope first. The write checkbox controls local database writes. A playlist limit supports small controlled tests. A full saved-library write requires the expected discovery count from a recent read-only preview. The page never changes YouTube. For collection followed by classification, use the corresponding CLI command with `--write`.

### Library Optimization

Analyzes the locally imported playlist inventory. It displays membership coverage, duplicate placement across regular playlists, empty or oversized playlists, uncategorized saved videos, and safe add recommendations. The button stores add-only recommendations in the local playlist plan. It does not execute YouTube actions.

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

The SQLite database can contain personal viewing metadata, saved playlist names, playlist memberships, transcripts, classifications, AI responses, and playlist plans. Treat it as private.

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

For normal operation, use `uv run ykm init-db`. It locks writers and creates a verified pre-migration backup when needed. Use raw Alembic commands only for development checks. Raw Alembic commands honor `YKM_DATABASE_URL` when it is set.

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

### Chrome or Edge cannot be found

Install Google Chrome, or set the browser channel to Microsoft Edge:

```powershell
YKM_BROWSER_CHANNEL=msedge
```

The manual Google login command does not support `YKM_BROWSER_CHANNEL=chromium`.

### Playwright Chromium is missing

```powershell
uv run playwright install chromium
```

### The profile is already in use

Exit every browser window created by `ykm browser-login`, synchronization, or playlist execution. The dedicated profile cannot be used by two browser processes simultaneously. If sync cannot attach, use the Chrome or Edge menu to exit the dedicated browser instead of closing only one tab.

Do not delete the profile unless you intend to lose its authenticated session.

### YouTube asks for login, consent, CAPTCHA, or account verification

The application should stop. Run:

```powershell
uv run ykm browser-login
```

Resolve the prompt manually. Exit the dedicated browser completely, press Enter in the terminal workflow, then retry the previous command. Do not add code that clicks through or bypasses the security control.

### The crawler reports zero videos

1. Run `browser-login`.
2. Confirm the dedicated profile can open `https://www.youtube.com/playlist?list=LL`.
3. Confirm the Liked Videos list contains visible items.
4. Keep `YKM_HEADLESS=false`.
5. Run `ykm sync` again.
6. If the page is visible but nothing is collected, YouTube may have changed its DOM. Review centralized selectors in `src/youtube_knowledge_manager/browser/selectors.py`.

Do not commit screenshots or page captures containing personal data. Create sanitized fixtures for regression tests.

### Playlist items time out while loading

Current versions retry playlist hydration up to three times. A visible Sign in link, CAPTCHA, consent screen, or security prompt stops the retry and requires manual intervention. If all three attempts fail without one of those prompts, exit the dedicated browser completely, verify the Liked Videos page loads normally, and rerun `uv run ykm sync`.

If the terminal still shows the raw Playwright message `Locator.wait_for: Timeout 60000ms exceeded`, update to the current working tree. The collector now replaces that raw error after bounded retries with an actionable `PlaylistLoadError`.

### The reported count is too low

Check whether YouTube says unavailable videos are hidden. The playlist header can include those entries while the collector cannot see or identify them. If that does not explain the difference, increase `YKM_MAX_SCROLLS` cautiously or increase `YKM_STABLE_SCROLL_LIMIT` in `.env`. Keep action delays conservative. Verify the end of the playlist manually. A low count can also indicate virtualized scrolling or a selector change.

### SQLite reports that the database is locked

Read the lock report, then close the named Streamlit or CLI process. If the recorded process is definitely gone, run `uv run ykm unlock --force`. The application never guesses that a lock is stale.

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
uv run pytest -m "not live_youtube" --cov=youtube_knowledge_manager --cov-report=term --cov-fail-under=75
uvx bandit -q -r src
```

CI also exports the frozen dependency graph for `pip-audit`, runs Alembic upgrade, schema-drift, and downgrade checks, and verifies CLI safety outcomes without depending on platform-specific terminal rendering.

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

- A complete authenticated read-only saved-library crawl discovered 85 playlists. Nineteen playlist count mismatches and intermittent four-card discovery remain under investigation.
- Live playlist dialogs have not completed controlled write validation.
- Unavailable playlist entries without a usable video ID may not be stored.
- Failed or private playlists are reported and skipped. They remain incomplete until a later successful crawl.
- Optimization is advisory and add only. Automatic merges, moves, removals, renames, and playlist creation are intentionally absent.
- Transcript extraction remains layout-dependent and best-effort. Persistence and retry state are idempotent.
- AI model pricing is operator supplied because provider prices change. The application enforces the configured timeout, retry, and token limits.
- Text search uses SQL `LIKE` rather than SQLite FTS5.
- Semantic embeddings and vector search are not implemented.
- Streamlit reports collection progress. Cancellation is cooperative. Bulk review is not implemented.
- Full readiness still requires reconciliation of the remaining live count mismatches, a repeatable full local import, representative Liked Videos checks, and one controlled live add-only action against an explicitly selected disposable target.

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
