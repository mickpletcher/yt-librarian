.PHONY: install browser migrate lint format typecheck test app sync

install:
	uv sync --all-extras

browser:
	uv run playwright install chromium

migrate:
	uv run alembic upgrade head

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy src

test:
	uv run pytest -m "not live_youtube"

app:
	uv run streamlit run src/youtube_knowledge_manager/ui/app.py

sync:
	uv run ykm sync
