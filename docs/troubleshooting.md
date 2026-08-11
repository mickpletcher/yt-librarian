# Troubleshooting

## The browser says the profile is in use

Exit every browser created by `ykm browser-login` or sync. The dedicated profile cannot be opened by two browser processes at once. Closing a tab is not enough if the dedicated browser is still running.

## Login or security intervention required

Run `uv run ykm browser-login`, handle the prompt manually in normal Chrome or Edge, exit that browser completely, and rerun the command. Never copy cookies into configuration.

## Google says the browser or app may not be secure

Do not sign in through an automated Playwright window. Set `YKM_BROWSER_CHANNEL=chrome` or `msedge`, then run `uv run ykm browser-login`. The login command starts the installed browser directly without an automation connection. After Liked Videos shows your account, exit the dedicated browser completely before running sync.

## Sync opens YouTube signed out after a successful login

Confirm login and sync use the same `YKM_BROWSER_PROFILE_DIR` and `YKM_BROWSER_CHANNEL`. The current sync implementation starts the installed browser with that profile and attaches through an ephemeral loopback-only debugging port. If an older dedicated browser process is still running, exit it completely and retry.

## No videos are found

Confirm the profile can open `https://www.youtube.com/playlist?list=LL`. The current collector supports both `ytd-playlist-video-renderer` and `yt-lockup-view-model`. YouTube may have changed its DOM again. Run the mocked test suite first, then inspect selectors in `browser/selectors.py` with a dry run.

## No saved playlists are found

Confirm the dedicated profile can open `https://www.youtube.com/feed/playlists` and displays the Playlists page while signed in. Exit the dedicated browser completely, then run `uv run ykm sync-library --limit-playlists 1`. If the page is visible but discovery still returns nothing, YouTube may have changed the playlist-card layout.

## Saved playlist discovery returns only a small partial count

YouTube can expose a small stable subset of the Playlists page without a continuation element. Run a read-only `uv run ykm sync-library` and compare its discovered count with the visible library. For a full local write, pass that verified count with `--expect-playlists`. If a later discovery differs, the app stops before processing an individual playlist. Exit the dedicated browser completely and retry. Do not lower the expected count to make a partial result pass.

## One saved playlist fails during a library sync

The all-library collector reports a normal playlist load failure and continues with the remaining playlists. It does not mark missing memberships inactive for the failed playlist. Exit the browser after the run, confirm that playlist opens normally, and rerun the read-only command. Login or security intervention is different and stops the full run immediately.

## The visible count is lower than the playlist header

Check for YouTube's unavailable-videos-hidden message. The header can include hidden entries while the page exposes no usable ID for them. Do not invent identifiers or treat hidden entries as collected. Reconcile the difference manually before declaring the crawl complete.

## Playlist item hydration times out

The collector retries this transient condition up to three times. It does not retry through login or security intervention. If every attempt fails, exit the dedicated browser completely, confirm the Liked Videos page loads normally, and rerun the read-only sync. Current code raises `PlaylistLoadError` after the final attempt instead of exposing the raw locator timeout.

## SQLite is locked

The single-writer lock reports the operation, process ID, and start time. Close the named Streamlit or CLI process. The app never removes a possibly active lock automatically. If the recorded process is definitely gone, run `uv run ykm unlock --force`.

## A playlist cannot be found

Ensure the local category playlist name exactly matches a visible YouTube playlist. If a playlist identifier is known, store it on the category. Planning will skip categories without either mapping.

Run a credible full preview, then use `uv run ykm sync-library --write --expect-playlists <verified-count>` to import current playlist IDs and memberships. Planning can then skip an addition already present in the known target playlist. Browser execution prefers the configured playlist ID when YouTube exposes IDs and otherwise requires one exact, unambiguous visible-name match. Use `uv run ykm apply-plan --validate --limit 1` to verify the dialog without changing YouTube.

## The database needs recovery

Run `uv run ykm db-check`. Create a verified backup with `uv run ykm db-backup`. Restore requires an explicit source and `--apply`; the command verifies the source and automatically creates a pre-restore backup of the active database. Keep all backup files private.

## Reset local state

Create a verified backup with `uv run ykm db-backup`. Remove only `data/youtube_knowledge_manager.sqlite3` if a clean local rebuild is intentional, then run `uv run ykm init-db`. Never delete the entire repository or browser profile as a troubleshooting shortcut.
