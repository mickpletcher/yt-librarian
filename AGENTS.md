# YouTube Knowledge Manager agent instructions

This Python 3.12+ project manages a local index of a user's YouTube Liked Videos and safely plans playlist assignments.

Read `assessment.md` before making changes. It is the current project baseline and risk register. If local `future-upgrades.md` exists, review it for scoped backlog items. Never force-add that file because it is intentionally local-only.

Keep browser automation, persistence, classification, planning, services, and UI separated. UI code must call services and repositories. Do not put SQL in UI code. Keep all YouTube selectors in `browser/selectors.py`.

Safety is part of the contract. Preserve dry-run defaults. Never add playlist deletion, Liked Videos removal, security-control bypasses, or rapid unthrottled actions. Stop for login, CAPTCHA, consent, and security challenges.

Never commit secrets, `.env`, browser profiles, cookies, storage state, databases, transcripts, logs, or personal YouTube data.

Commands:

```text
uv sync --all-extras
uv run playwright install chromium
uv run alembic upgrade head
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -m "not live_youtube"
uv run streamlit run src/youtube_knowledge_manager/ui/app.py
```

Add or update tests for every behavior change. Mock YouTube in normal tests. Mark real-account tests `live_youtube`; CI must never run them automatically.

Every repository change must update `CHANGELOG.md`, `README.md`, and `assessment.md` in the same change set. Record what changed in `CHANGELOG.md`. Keep README behavior and commands current. Update assessment findings, verification evidence, risks, readiness, and next steps when affected. A documentation-only change still requires all three files to be reviewed and updated.

When implementing an item from `future-upgrades.md`, preserve its upgrade ID, remove the full item from `future-upgrades.md`, and add it to `completed-upgrades.md` with the completion date, shipped scope, files changed, and verification results. The same item must not remain in both files. Keep `completed-upgrades.md`, `CHANGELOG.md`, `README.md`, and `assessment.md` aligned before closing the change.
