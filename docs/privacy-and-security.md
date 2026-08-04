# Privacy and security

All personal data is local by default. Git ignores databases, browser profiles, cookies, storage-state exports, transcripts, logs, private configuration, and generated reports.

The application never asks for or stores a Google password. Authentication happens in Google's own pages inside the dedicated Playwright profile. Do not share that profile because it contains authenticated session material.

AI is disabled by default. Enabling it sends selected titles, descriptions, channel names, and optional transcript text to the configured provider. Review the provider's retention terms before enabling it. API keys belong in environment variables or a private `.env` file.

No feature bypasses CAPTCHA, rate limits, consent, login, or account-security checks. The browser stops for manual intervention. Playlist removal, playlist deletion, and removal from Liked Videos are intentionally absent.

The Docker configuration runs the local UI in dry-run mode. Interactive authenticated browser automation is recommended on the host, not in the container.
