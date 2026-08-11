from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

import youtube_knowledge_manager.cli as cli
from youtube_knowledge_manager.settings import Settings

runner = CliRunner()


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{(tmp_path / 'app.sqlite3').as_posix()}",
        browser_profile_dir=tmp_path / "profile",
    )


def test_database_cli_lifecycle(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    settings = _settings(tmp_path)
    monkeypatch.setattr(cli, "_settings", lambda: settings)
    monkeypatch.setattr(
        cli,
        "_backup_name",
        lambda prefix: tmp_path / f"{prefix}.sqlite3",
    )

    initialized = runner.invoke(cli.app, ["init-db"])
    assert initialized.exit_code == 0, initialized.output

    checked = runner.invoke(cli.app, ["db-check"])
    assert checked.exit_code == 0, checked.output
    assert "Integrity ok" in checked.output

    manual_backup = tmp_path / "manual.sqlite3"
    backed_up = runner.invoke(
        cli.app,
        ["db-backup", "--destination", str(manual_backup)],
    )
    assert backed_up.exit_code == 0, backed_up.output
    assert manual_backup.is_file()

    preview = runner.invoke(cli.app, ["db-restore", str(manual_backup)])
    assert preview.exit_code != 0
    assert manual_backup.is_file()

    restored = runner.invoke(cli.app, ["db-restore", str(manual_backup), "--apply"])
    assert restored.exit_code == 0, restored.output
    assert (tmp_path / "pre-restore.sqlite3").is_file()


def test_sync_preview_and_apply_preview_do_not_open_browser(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    settings = _settings(tmp_path)
    monkeypatch.setattr(cli, "_settings", lambda: settings)
    assert runner.invoke(cli.app, ["init-db"]).exit_code == 0
    received: list[bool] = []

    class SynchronizationService:
        def __init__(self, *_: object) -> None:
            pass

        async def run(self, *, dry_run: bool, **_: object):  # type: ignore[no-untyped-def]
            received.append(dry_run)
            return SimpleNamespace(seen=2, created=0, changed=0, dry_run=dry_run)

    monkeypatch.setattr(cli, "SynchronizationService", SynchronizationService)

    synced = runner.invoke(cli.app, ["sync"])
    assert synced.exit_code == 0, synced.output
    assert received == [True]

    apply_preview = runner.invoke(cli.app, ["apply-plan"])
    assert apply_preview.exit_code == 0, apply_preview.output
    assert "No browser writes performed" in apply_preview.output


def test_full_library_write_requires_expected_count_before_setup(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    settings_loaded = False

    def load_settings() -> Settings:
        nonlocal settings_loaded
        settings_loaded = True
        return Settings()

    monkeypatch.setattr(cli, "_settings", load_settings)

    result = runner.invoke(cli.app, ["sync-library", "--write"])

    assert result.exit_code != 0
    assert settings_loaded is False
