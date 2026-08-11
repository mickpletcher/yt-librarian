from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.orm import Session

from youtube_knowledge_manager.browser.external import launch_external_browser
from youtube_knowledge_manager.browser.profile import validate_profile_directory
from youtube_knowledge_manager.browser.session import BrowserSession, ManualInterventionRequired
from youtube_knowledge_manager.classification.ai_provider import AIProvider
from youtube_knowledge_manager.classification.classifier import ClassificationEngine
from youtube_knowledge_manager.classification.local_provider import LocalProvider
from youtube_knowledge_manager.classification.openai_provider import OpenAIProvider
from youtube_knowledge_manager.classification.rules import RulesEngine, load_rules
from youtube_knowledge_manager.collection.crawler import (
    CrawlSummary,
    IncompletePlaylistCrawlError,
)
from youtube_knowledge_manager.collection.enrichment import EnrichmentService
from youtube_knowledge_manager.collection.library_synchronization import (
    IncompletePlaylistLibraryError,
    LibrarySynchronizationService,
    LibrarySyncProgress,
)
from youtube_knowledge_manager.collection.synchronization import SynchronizationService
from youtube_knowledge_manager.db.repositories import BrowserActionRepository, VideoRepository
from youtube_knowledge_manager.db.session import create_database_engine, create_session_factory
from youtube_knowledge_manager.logging_config import configure_logging
from youtube_knowledge_manager.operations.locking import (
    ApplicationLock,
    remove_lock,
    sqlite_database_path,
)
from youtube_knowledge_manager.planning.executor import PlaylistPlanExecutor
from youtube_knowledge_manager.planning.playlist_plan import PlaylistPlanner
from youtube_knowledge_manager.search.text_search import TextSearchService
from youtube_knowledge_manager.services.category_service import CategoryService, load_categories
from youtube_knowledge_manager.services.classification_service import ClassificationService
from youtube_knowledge_manager.services.database_operations import (
    backup_database,
    check_database,
    restore_database,
)
from youtube_knowledge_manager.services.library_optimization import LibraryOptimizationService
from youtube_knowledge_manager.services.privacy_inventory import collect_privacy_inventory
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


def _database_revision(settings: Settings) -> str | None:
    engine = create_database_engine(settings.database_url)
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def _head_revision() -> str:
    return str(ScriptDirectory.from_config(Config("alembic.ini")).get_current_head())


def _require_database_current(settings: Settings) -> None:
    database_path = sqlite_database_path(settings.database_url)
    if not database_path.is_file():
        raise RuntimeError("Database is not initialized. Run `ykm init-db` first.")
    current = _database_revision(settings)
    if current != _head_revision():
        raise RuntimeError("Database migration is pending. Run `ykm init-db` first.")


def _backup_name(prefix: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path("data/backups") / f"{prefix}-{stamp}.sqlite3"


def _ai_provider(settings: Settings) -> AIProvider | None:
    if settings.ai_provider == "openai":
        return OpenAIProvider(
            settings.ai_model,
            timeout_seconds=settings.ai_timeout_seconds,
            max_retries=settings.ai_max_retries,
        )
    if settings.ai_provider == "local":
        return LocalProvider(
            settings.ai_model,
            settings.ai_base_url,
            timeout_seconds=settings.ai_timeout_seconds,
            max_retries=settings.ai_max_retries,
        )
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
    with ApplicationLock(settings.database_url, operation="database migration"):
        database_path = sqlite_database_path(settings.database_url)
        current = _database_revision(settings) if database_path.is_file() else None
        if current is not None and current != _head_revision():
            backup_path = backup_database(settings.database_url, _backup_name("pre-migration"))
            typer.echo(f"Pre-migration backup verified: {backup_path}")
        _upgrade_database(settings)
        with create_session_factory(settings)() as session:
            _prepare_data(settings, session)
    typer.echo("Database and categories are ready.")


@app.command("browser-login")
def browser_login() -> None:
    """Open the dedicated profile for manual YouTube authentication."""
    settings = _settings()

    async def run() -> None:
        if settings.browser_channel == "chromium":
            raise RuntimeError(
                "Manual Google sign-in requires YKM_BROWSER_CHANNEL=chrome or msedge."
            )
        profile_dir = validate_profile_directory(settings.browser_profile_dir)
        with ApplicationLock(settings.database_url, operation="browser login"):
            launched = await launch_external_browser(
                settings.browser_channel,
                profile_dir,
                "https://www.youtube.com/playlist?list=LL",
                enable_debugging=False,
                headless=False,
            )
            typer.echo("Sign in or resolve prompts manually in the normal browser window.")
            await asyncio.to_thread(
                input,
                "Close that browser window completely, then press Enter here: ",
            )
            if launched.process.returncode is None:
                typer.echo(
                    "The browser process is still running. Exit it completely before running sync."
                )

    asyncio.run(run())


@app.command()
def sync(
    write: Annotated[
        bool, typer.Option("--write", help="Persist discoveries. Default is a read-only preview.")
    ] = False,
) -> None:
    """Crawl Liked Videos and process only new or changed metadata."""
    settings = _settings()
    _require_database_current(settings)
    with ApplicationLock(settings.database_url, operation="liked videos synchronization"):
        with create_session_factory(settings)() as session:
            if write:
                _prepare_data(settings, session)

            def report(progress: CrawlSummary) -> None:
                if progress.seen % 100 == 0:
                    typer.echo(
                        f"Progress: {progress.seen} seen; {progress.created} created; "
                        f"{progress.changed} changed."
                    )

            try:
                summary = asyncio.run(
                    SynchronizationService(settings, session).run(
                        dry_run=not write,
                        progress=report,
                    )
                )
            except IncompletePlaylistCrawlError as exc:
                typer.echo(f"Error: {exc}", err=True)
                raise typer.Exit(code=1) from exc
            typer.echo(
                f"Seen {summary.seen}; created {summary.created}; changed {summary.changed}; "
                f"dry_run={summary.dry_run}"
            )
            if write:
                processed = ClassificationService(
                    settings, session, _classification_engine(settings)
                ).classify_pending(limit=10_000, write=True)
                typer.echo(f"Classified {processed} new or changed videos.")


@app.command("sync-library")
def sync_library(
    write: Annotated[
        bool,
        typer.Option("--write", help="Persist playlists, memberships, and videos locally."),
    ] = False,
    limit_playlists: Annotated[
        int | None,
        typer.Option(
            "--limit-playlists",
            min=1,
            help="Limit playlist count for controlled validation. Default scans all.",
        ),
    ] = None,
    expect_playlists: Annotated[
        int | None,
        typer.Option(
            "--expect-playlists",
            min=1,
            help="Require this exact discovery count before processing any playlist.",
        ),
    ] = None,
) -> None:
    """Crawl every visible saved playlist and its videos."""
    if write and limit_playlists is None and expect_playlists is None:
        raise typer.BadParameter(
            "A full write requires the exact discovery count from a recent preview.",
            param_hint="--expect-playlists",
        )
    settings = _settings()
    _require_database_current(settings)
    with ApplicationLock(settings.database_url, operation="saved library synchronization"):
        with create_session_factory(settings)() as session:
            if write:
                _prepare_data(settings, session)

            def report(progress: LibrarySyncProgress) -> None:
                typer.echo(
                    f"Progress: playlists {progress.playlists_completed}/"
                    f"{progress.playlists_total}; memberships {progress.memberships_seen}."
                )

            try:
                summary = asyncio.run(
                    LibrarySynchronizationService(settings, session).run(
                        dry_run=not write,
                        limit_playlists=limit_playlists,
                        expected_playlist_count=expect_playlists,
                        progress=report,
                    )
                )
            except IncompletePlaylistLibraryError as exc:
                typer.echo(f"Error: {exc}", err=True)
                raise typer.Exit(code=1) from exc
            typer.echo(
                f"Discovery complete {summary.discovery_complete}; "
                f"discovered {summary.playlists_discovered}; "
                f"processed {summary.playlists_seen}; failed {summary.playlists_failed}; "
                f"memberships {summary.memberships_seen}; "
                f"unique videos {summary.unique_videos_seen}; "
                f"videos created {summary.videos_created}; "
                f"videos changed {summary.videos_changed}; "
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
    _require_database_current(settings)
    with ApplicationLock(settings.database_url, operation="classification"):
        with create_session_factory(settings)() as session:
            _prepare_data(settings, session)
            processed = ClassificationService(
                settings, session, _classification_engine(settings)
            ).classify_pending(limit=limit, write=write)
            typer.echo(f"Processed {processed} videos; write={write}.")


@app.command()
def enrich(
    write: Annotated[
        bool,
        typer.Option("--write", help="Persist metadata and transcript enrichment."),
    ] = False,
    include_transcripts: Annotated[
        bool,
        typer.Option("--transcripts/--no-transcripts"),
    ] = True,
    limit: Annotated[int, typer.Option(min=1, max=10_000)] = 100,
) -> None:
    """Enrich pending videos with resumable metadata and transcript state."""
    settings = _settings()
    _require_database_current(settings)
    with create_session_factory(settings)() as session:
        videos = VideoRepository(session).list_for_enrichment(limit=limit)
        if not write:
            typer.echo(f"{len(videos)} videos eligible for enrichment. No browser opened.")
            return

        async def run() -> tuple[int, int]:
            completed = 0
            failed = 0
            async with BrowserSession(settings) as browser:
                service = EnrichmentService(session, browser)
                for index, video in enumerate(videos, start=1):
                    try:
                        await service.enrich(video, include_transcript=include_transcripts)
                        completed += 1
                    except ManualInterventionRequired:
                        raise
                    except Exception:
                        failed += 1
                    typer.echo(
                        f"Enrichment progress {index}/{len(videos)}; "
                        f"complete {completed}; failed {failed}."
                    )
            return completed, failed

        with ApplicationLock(settings.database_url, operation="video enrichment"):
            completed, failed = asyncio.run(run())
        typer.echo(f"Enrichment complete {completed}; failed {failed}.")


@app.command()
def plan(
    write: Annotated[
        bool, typer.Option("--write", help="Persist proposed actions. Default is preview only.")
    ] = False,
) -> None:
    """Create idempotent playlist-add actions from approved assignments."""
    settings = _settings()
    _require_database_current(settings)
    with ApplicationLock(settings.database_url, operation="playlist planning"):
        with create_session_factory(settings)() as session:
            summary, _ = PlaylistPlanner(session).generate(dry_run=not write, persist=write)
        typer.echo(
            f"Eligible {summary.eligible_assignments}; new {summary.created_actions}; "
            f"existing {summary.existing_actions}; already present {summary.already_present}; "
            f"unmapped {summary.skipped_unmapped}; write={write}"
        )


@app.command("optimize-library")
def optimize_library(
    oversized_threshold: Annotated[
        int,
        typer.Option(
            "--oversized-threshold",
            min=1,
            help="Flag regular playlists with more than this many active videos.",
        ),
    ] = 500,
    write_plan: Annotated[
        bool,
        typer.Option(
            "--write-plan",
            help="Persist add-only playlist recommendations. Does not change YouTube.",
        ),
    ] = False,
) -> None:
    """Analyze saved-playlist organization and add-only recommendations."""
    settings = _settings()
    _require_database_current(settings)
    with create_session_factory(settings)() as session:
        report = LibraryOptimizationService(session).analyze(
            oversized_threshold=oversized_threshold
        )
        summary = report.summary
        typer.echo(
            f"Playlists {summary.playlist_count}; memberships {summary.active_membership_count}; "
            f"unique videos {summary.unique_video_count}; cross-playlist duplicates "
            f"{summary.duplicate_regular_video_count}; uncategorized "
            f"{summary.uncategorized_video_count}; empty regular playlists "
            f"{summary.empty_regular_playlist_count}; oversized playlists "
            f"{summary.oversized_playlist_count}; recommended additions "
            f"{summary.recommended_addition_count}."
        )
        for row in report.oversized_playlists:
            typer.echo(f"Oversized: {row.playlist.name} ({row.active_video_count} videos)")
        if write_plan:
            with ApplicationLock(settings.database_url, operation="optimization planning"):
                plan_summary, _ = PlaylistPlanner(session).generate(dry_run=False, persist=True)
            typer.echo(
                f"Plan stored: new {plan_summary.created_actions}; existing "
                f"{plan_summary.existing_actions}; already present "
                f"{plan_summary.already_present}; unmapped {plan_summary.skipped_unmapped}."
            )


@app.command("apply-plan")
def apply_plan(
    apply: Annotated[
        bool, typer.Option("--apply", help="Perform pending YouTube playlist additions.")
    ] = False,
    validate: Annotated[
        bool,
        typer.Option("--validate", help="Open dialogs and verify targets without selecting them."),
    ] = False,
    limit: Annotated[int, typer.Option(min=1, max=1000)] = 100,
) -> None:
    """Apply approved playlist additions. Without --apply, only report the queue."""
    settings = _settings()
    _require_database_current(settings)
    if apply and validate:
        raise typer.BadParameter("Choose either --apply or --validate")
    with create_session_factory(settings)() as session:
        pending = BrowserActionRepository(session).list_pending(limit=limit)
        if not apply and not validate:
            typer.echo(f"{len(pending)} pending actions. No browser writes performed.")
            return
        with ApplicationLock(settings.database_url, operation="playlist execution"):
            executor = PlaylistPlanExecutor(settings, session)
            summary = asyncio.run(
                executor.execute(limit=limit) if apply else executor.validate(limit=limit)
            )
        typer.echo(
            f"Attempted {summary.attempted}; succeeded {summary.succeeded}; "
            f"already present {summary.already_present}; failed {summary.failed}."
        )


@app.command("search")
def search_command(
    query: Annotated[str, typer.Argument(help="Text to find in titles, descriptions, or channels")],
    category: Annotated[str | None, typer.Option("--category")] = None,
) -> None:
    """Search the local index."""
    settings = _settings()
    _require_database_current(settings)
    with create_session_factory(settings)() as session:
        for result in TextSearchService(session).search(query, category_slug=category):
            typer.echo(f"{result.title}\n  {result.canonical_url}")


@app.command("db-check")
def db_check() -> None:
    """Run SQLite integrity checks without changing data."""
    settings = _settings()
    _require_database_current(settings)
    result = check_database(settings.database_url)
    typer.echo(
        f"Integrity {result.integrity}; pages {result.page_count}; "
        f"free pages {result.freelist_count}."
    )


@app.command("db-backup")
def db_backup(
    destination: Annotated[Path | None, typer.Option("--destination")] = None,
) -> None:
    """Create and verify a consistent SQLite backup."""
    settings = _settings()
    _require_database_current(settings)
    target = destination or _backup_name("manual")
    with ApplicationLock(settings.database_url, operation="database backup"):
        created = backup_database(settings.database_url, target)
    typer.echo(f"Backup verified: {created}")


@app.command("db-restore")
def db_restore(
    source: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    apply: Annotated[bool, typer.Option("--apply", help="Replace the active database.")] = False,
) -> None:
    """Verify a backup and restore it only with --apply."""
    settings = _settings()
    if not apply:
        raise typer.BadParameter("Restore requires --apply")
    with ApplicationLock(settings.database_url, operation="database restore"):
        database_path = sqlite_database_path(settings.database_url)
        if database_path.is_file():
            safety_backup = backup_database(settings.database_url, _backup_name("pre-restore"))
            typer.echo(f"Pre-restore backup verified: {safety_backup}")
        restored = restore_database(settings.database_url, source, apply=True)
    typer.echo(f"Restore verified: {restored}")


@app.command("data-inventory")
def data_inventory(
    output: Annotated[Path | None, typer.Option("--output")] = None,
) -> None:
    """Report private local data as counts only, with an optional sanitized JSON file."""
    settings = _settings()
    _require_database_current(settings)
    with create_session_factory(settings)() as session:
        inventory = collect_privacy_inventory(session)
    payload = inventory.sanitized_payload()
    typer.echo(json.dumps(payload, sort_keys=True))
    if output is not None:
        destination = output.expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(f"{destination.suffix}.tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(destination)
        typer.echo("Sanitized inventory written.")


@app.command("unlock")
def unlock(
    force: Annotated[bool, typer.Option("--force")] = False,
) -> None:
    """Remove a stale application lock after confirming no operation is active."""
    settings = _settings()
    removed = remove_lock(settings.database_url, force=force)
    typer.echo("Stale lock removed." if removed else "No lock exists.")


if __name__ == "__main__":
    app()
