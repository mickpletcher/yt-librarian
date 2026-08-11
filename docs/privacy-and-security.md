# Privacy and security

All personal data is local by default. The database can contain saved playlist names, video memberships, viewing metadata, classifications, and transcripts. Git ignores databases, browser profiles, cookies, storage-state exports, transcripts, logs, private configuration, and generated reports.

The application never asks for or stores a Google password. Authentication happens in Google's own pages in normal Chrome or Edge using the dedicated project profile. Automated reads later attach to that same profile through a loopback-only connection. Do not share the profile because it contains authenticated session material.

AI is disabled by default. Enabling it sends selected titles, descriptions, channel names, and optional transcript text to the configured provider. Review the provider's retention terms before enabling it. API keys belong in environment variables or a private `.env` file.

Remote AI calls have bounded timeouts and retries plus a daily token ceiling. A zero token limit disables AI calls. Preview classification is deterministic-only because provider usage cannot be durably counted without local writes. Estimated cost uses operator-supplied per-million-token rates. The local provider accepts only loopback HTTP or HTTPS endpoints. Deterministic rules continue when the AI budget is exhausted or the provider fails.

No feature bypasses CAPTCHA, rate limits, consent, login, or account-security checks. The browser stops for manual intervention. Optimization is local and advisory. Playlist removal, playlist deletion, automatic moves or merges, and removal from Liked Videos are intentionally absent.

`ykm data-inventory` reports counts only. Its optional JSON output contains a schema version and table counts, never titles, URLs, playlist names, transcript text, browser paths, credentials, or provider responses. Database backups remain private and exclude browser authentication state because only SQLite is copied through its supported backup API.

The Docker configuration runs the local UI in dry-run mode. Interactive authenticated browser automation is recommended on the host, not in the container.
