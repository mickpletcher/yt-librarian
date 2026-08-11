# Browser automation

The app uses a dedicated persistent Chrome or Edge profile. `ykm browser-login` starts the installed browser directly, without Playwright or remote debugging, so authentication stays entirely in the normal browser. Authenticate manually, confirm Liked Videos is visible, and exit the dedicated browser completely before synchronization.

For synchronization and playlist execution, the app starts the same installed browser and profile with an ephemeral debugging port bound only to `127.0.0.1`. Playwright attaches after the browser starts. This reuses the authenticated session without automating Google sign-in or exporting cookies. Chrome 136 and newer require a non-default `--user-data-dir` for remote debugging; the project profile satisfies that isolation requirement.

Selectors are centralized in `src/youtube_knowledge_manager/browser/selectors.py`. YouTube DOM changes should be handled there first. The collector supports the classic playlist renderer, current lockup view model, and current continuation item view model. It recognizes watch, Shorts, and live URLs and extracts the canonical video ID, URL, title, channel, thumbnail, position, and visible availability state. Individual playlist collection accepts only video links whose `list` parameter identifies the current playlist, preventing recommendation rows from entering membership inventory. Each visible batch is read in one browser evaluation. The collector progressively scrolls until the unique visible set stops growing or the configured limit is reached.

All-library collection starts at `https://www.youtube.com/feed/playlists`. It progressively discovers saved playlist cards, extracts stable playlist IDs, names, URLs, and displayed counts, then opens each playlist through the same generic video collector. Liked Videos and Watch Later use their normal system IDs. Empty playlists are recorded without attempting a video crawl.

The YouTube playlist header can include unavailable videos that the page hides. Those entries cannot be collected without a visible usable video ID. Full validation must reconcile that difference separately from selector or scroll failures.

Playlist hydration is retried up to three times because YouTube can commit navigation before its item models appear. Every attempt rechecks the fail-closed login, CAPTCHA, consent, and account-security boundaries. A recognized intervention stops immediately; retries never click through a prompt.

Before and during operations, the session checks for CAPTCHA frames, Google challenge URLs, login pages, consent screens, and unexpected account prompts. Detection raises a manual-intervention error. The app does not click through or bypass these controls.

Playlist writes follow this sequence:

1. Open the video.
2. Open the Save dialog.
3. When a playlist ID is configured, require the dialog to expose and match that ID. A missing or different ID fails closed.
4. Only when no ID is configured, require one unambiguous exact visible-name match. Duplicate names fail closed.
5. If already selected, record success without clicking.
6. In validation mode, close the dialog without selecting anything.
7. In apply mode only, select it and verify the checked state.

Random delays are applied between actions. Keep the default conservative values. Dry-run is the default for sync and playlist execution.

`ykm sync-library` is read only by default. `--write` changes only local SQLite. A full write requires `--expect-playlists` from a recent preview. A mismatch stops before individual playlist processing, which fails closed when the Playlists page exposes an incomplete stable view. An individual playlist load or count-reconciliation failure is reported and does not stop unrelated playlists, but a login or security intervention stops the run. No collection or optimization command removes, moves, merges, renames, creates, or deletes YouTube content.

Live tests require a real account and are marked `live_youtube`. They are never part of CI. Mocked tests cover scrolling, incomplete-crawl preservation, authentication and security stops, playlist lookup, already-present handling, action recovery, and loopback-only browser startup.
