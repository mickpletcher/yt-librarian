#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
exec uv run streamlit run src/youtube_knowledge_manager/ui/app.py "$@"
