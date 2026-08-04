#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
uv sync --all-extras
uv run playwright install chromium
[ -f .env ] || cp .env.example .env
[ -f config/categories.yaml ] || cp config/categories.example.yaml config/categories.yaml
[ -f config/rules.yaml ] || cp config/rules.example.yaml config/rules.yaml
uv run alembic upgrade head
printf '%s\n' 'Setup complete. Run: uv run ykm browser-login'
