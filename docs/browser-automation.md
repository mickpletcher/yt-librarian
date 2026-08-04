# Browser automation

The app launches a dedicated persistent Chromium profile. Run `ykm browser-login`, authenticate manually, and close the browser before synchronization.

Selectors are centralized in `src/youtube_knowledge_manager/browser/selectors.py`. YouTube DOM changes should be handled there first. The crawler extracts the canonical video ID, URL, title, channel, thumbnail, position, and visible availability state. It progressively scrolls until the visible set stops growing or the configured limit is reached.

Before and during operations, the session checks for CAPTCHA frames, Google challenge URLs, login pages, consent screens, and unexpected account prompts. Detection raises a manual-intervention error. The app does not click through or bypass these controls.

Playlist writes follow this sequence:

1. Open the video.
2. Open the Save dialog.
3. Find the target playlist by exact visible name.
4. If already selected, record success without clicking.
5. In apply mode only, select it and verify the checked state.

Random delays are applied between actions. Keep the default conservative values. Dry-run is the default for sync and playlist execution.

Live tests require a real account and are marked `live_youtube`. They are never part of CI.
