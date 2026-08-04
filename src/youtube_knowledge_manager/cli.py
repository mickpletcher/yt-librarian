from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from youtube_knowledge_manager.browser.session import BrowserSession
from youtube_knowledge_manager.classification.ai_provider import AIProvider
from youtube_knowledge_manager.classification.classifier import ClassificationEngine
from youtube_knowledge_manager.classification.local_provider import LocalProvider
from youtube_knowledge_manager.classification.openai_provider import OpenAIProvider
from youtube_knowledge_manager.classification.rules import RulesEngine, load_rules
from youtube_knowledge_manager.collection.synchronization import SynchronizationService
from youtube_knowledge_manager.db.repositories import BrowserActionRepository
from youtube_knowledge_manager.db.session import create_session_factory
from youtube_knowledge_manager.logging_config import configure_logging
from youtube_knowledge_manager.planning.executor import PlaylistPlanExecutor
from youtube_knowledge_manager.planning.playlist_plan import PlaylistPlanner
from youtube_knowledge_manager.search.text_search import TextSearchService
from youtube_knowledge_manager.services.category_service import CategoryService, load_categories
from youtube_knowledge_manager.services.classification_service import ClassificationService
from youtube_knowledge_manager.settings import Settings, get_settings

app = typer.Typer(no_args_is_help=True, help="Local-first YouTube Knowledge Manager")


def _settings() -> Settings:
    settings = get_settings()
    settings.prepare_local_directories()
    configure_logging(settings.log_level)
    return settings


def _config_path(configured: Path, example_name: str) -> Path:
    if configured.exists():
        return configured
    example = Path("config") / example_name
    if example.exists():
        return example
    raise FileNotFoundError(f"Configuration not found: {configured}")


def _upgrade_database(settings: Settings) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")


def _ai_provider(settings: Settings) -> AIProvider | None:
    if settings.ai_provider == "openai":
        return OpenAIProvider(settings.ai_model)
    if settings.ai_provider == "local":
        return LocalProvider(settings.ai_model, settings.ai_base_url)
    return None


def _classification_engine(settings: Settings) -> ClassificationEngine:
    categories_path = _config_path(settings.categories_path, "categories.example.yaml")
    rules_path = _config_path(settings.rules_path, "rules.example.yaml")
    return ClassificationEngine(
        RulesEngine(load_rules(rules_path)),
        load_categories(categories_path),
        _ai_provider(settings),
    )


def _prepare_data(settings: Settings, session: Session) -> None:
    categories_path = _config_path(settings.categories_path, "categories.example.yaml")
    CategoryService(session).synchronize(categories_path)


@app.command("init-db")
def init_db() -> None:
    """Create or migrate the local database."""
    settings = _settings()
    _upgrade_database(settings)
    with create_session_factory(settings)() as session:
        _prepare_data(settings, session)
    typer.echo("Database and categories are ready.")


@app.command("browser-login")
def browser_login() -> None:
    """Open the dedicated profile for manual YouTube authentication."""
    settings = _settings()

    async def run() -> None:
        async with BrowserSession(settings, login_mode=True) as browser:
            page = browser.require_page()
            await page.goto("https://www.youtube.com/playlist?list=LL")
            typer.echo("Sign in or resolve prompts manually in the browser.")
            await asyncio.to_thread(input, "Press Enter here when finished: ")

    asyncio.run(run())


@app.command()
def sync(
    write: Annotated[
        bool, typer.Option("--write", help="Persist discoveries. Default is a read-only preview.")
    ] = False,
) -> None:
    """Crawl Liked Videos and process only new or changed metadata."""
    settings = _settings()
    if write:
        _upgrade_database(settings)
    with create_session_factory(settings)() as session:
        if write:
            _prepare_data(settings, session)
        summary = asyncio.run(SynchronizationService(settings, session).run(dry_run=not write))
        typer.echo(
            f"Seen {summary.seen}; created {summary.created}; changed {summary.changed}; "
            f"dry_run={summary.dry_run}"
        )
        if write:
            processed = ClassificationService(
                settings, session, _classification_engine(settings)
            ).classify_pending(limit=10_000, write=True)
            typer.echo(f"Classified {processed} new or changed videos.")


@app.command()
def classify(
    write: Annotated[
        bool, typer.Option("--write", help="Persist assignments. Default is preview only.")
    ] = False,
    limit: Annotated[int, typer.Option(min=1, max=10_000)] = 100,
) -> None:
    """Classify pending videos with rules and the configured optional AI provider."""
    settings = _settings()
    _upgrade_database(settings)
    with create_session_factory(settings)() as session:
        _prepare_data(settings, session)
        processed = ClassificationService(
            settings, session, _classification_engine(settings)
        ).classify_pending(limit=limit, write=write)
        typer.echo(f"Processed {processed} videos; write={write}.")


@app.command()
def plan(
    write: Annotated[
        bool, typer.Option("--write", help="Persist proposed actions. Default is preview only.")
    ] = False,
) -> None:
    """Create idempotent playlist-add actions from approved assignments."""
    settings = _settings()
    _upgrade_database(settings)
    with create_session_factory(settings)() as session:
        summary, _ = PlaylistPlanner(session).generate(dry_run=not write, persist=write)
        typer.echo(
            f"Eligible {summary.eligible_assignments}; new {summary.created_actions}; "
            f"existing {summary.existing_actions}; unmapped {summary.skipped_unmapped}; "
            f"write={write}"
        )


@app.command("apply-plan")
def apply_plan(
    apply: Annotated[
        bool, typer.Option("--apply", help="Perform pending YouTube playlist additions.")
    ] = False,
    limit: Annotated[int, typer.Option(min=1, max=1000)] = 100,
) -> None:
    """Apply approved playlist additions. Without --apply, only report the queue."""
    settings = _settings()
    _upgrade_database(settings)
    with create_session_factory(settings)() as session:
        pending = BrowserActionRepository(session).list_pending(limit=limit)
        if not apply:
            typer.echo(f"{len(pending)} pending actions. No browser writes performed.")
            return
        summary = asyncio.run(PlaylistPlanExecutor(settings, session).execute(limit=limit))
        typer.echo(
            f"Attempted {summary.attempted}; succeeded {summary.succeeded}; "
            f"failed {summary.failed}."
        )


@app.command("search")
def search_command(
    query: Annotated[str, typer.Argument(help="Text to find in titles, descriptions, or channels")],
    category: Annotated[str | None, typer.Option("--category")] = None,
) -> None:
    """Search the local index."""
    settings = _settings()
    _upgrade_database(settings)
    with create_session_factory(settings)() as session:
        for result in TextSearchService(session).search(query, category_slug=category):
            typer.echo(f"{result.title}\n  {result.canonical_url}")


if __name__ == "__main__":
    app()
