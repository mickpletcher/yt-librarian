from __future__ import annotations

import asyncio
import os
import shutil
import socket
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from playwright.async_api import Browser, Error, Playwright

BrowserChannel = Literal["chrome", "msedge"]


@dataclass(frozen=True)
class ExternalBrowserProcess:
    process: asyncio.subprocess.Process
    debugging_port: int | None


def _browser_candidates(channel: BrowserChannel) -> tuple[Path | str, ...]:
    if sys.platform == "win32":
        program_files = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        program_files_x86 = Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
        if channel == "chrome":
            return (
                program_files / "Google/Chrome/Application/chrome.exe",
                program_files_x86 / "Google/Chrome/Application/chrome.exe",
                local_app_data / "Google/Chrome/Application/chrome.exe",
                "chrome.exe",
            )
        return (
            program_files / "Microsoft/Edge/Application/msedge.exe",
            program_files_x86 / "Microsoft/Edge/Application/msedge.exe",
            local_app_data / "Microsoft/Edge/Application/msedge.exe",
            "msedge.exe",
        )
    if sys.platform == "darwin":
        if channel == "chrome":
            return (
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                "google-chrome",
            )
        return (
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            "microsoft-edge",
        )
    if channel == "chrome":
        return ("google-chrome", "google-chrome-stable", "chrome")
    return ("microsoft-edge", "microsoft-edge-stable", "msedge")


def find_browser_executable(channel: BrowserChannel) -> Path:
    for candidate in _browser_candidates(channel):
        if isinstance(candidate, Path):
            if candidate.is_file():
                return candidate.resolve()
            continue
        discovered = shutil.which(candidate)
        if discovered is not None:
            return Path(discovered).resolve()
    raise FileNotFoundError(f"Could not find {channel}. Install it or change YKM_BROWSER_CHANNEL.")


def reserve_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def build_browser_command(
    executable: Path,
    profile_dir: Path,
    initial_url: str,
    *,
    debugging_port: int | None,
    headless: bool,
) -> list[str]:
    command = [
        str(executable),
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if debugging_port is not None:
        command.extend(
            [
                "--remote-debugging-address=127.0.0.1",
                f"--remote-debugging-port={debugging_port}",
            ]
        )
    if headless:
        command.append("--headless=new")
    command.append(initial_url)
    return command


async def launch_external_browser(
    channel: BrowserChannel,
    profile_dir: Path,
    initial_url: str,
    *,
    enable_debugging: bool,
    headless: bool,
) -> ExternalBrowserProcess:
    executable = find_browser_executable(channel)
    debugging_port = reserve_loopback_port() if enable_debugging else None
    command = build_browser_command(
        executable,
        profile_dir,
        initial_url,
        debugging_port=debugging_port,
        headless=headless,
    )
    if sys.platform == "win32":
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
    return ExternalBrowserProcess(process=process, debugging_port=debugging_port)


async def connect_to_external_browser(
    playwright: Playwright,
    launched: ExternalBrowserProcess,
    *,
    timeout_seconds: float = 30.0,
) -> Browser:
    if launched.debugging_port is None:
        raise ValueError("External browser was launched without local debugging enabled")
    endpoint = f"http://127.0.0.1:{launched.debugging_port}"
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    last_error: Error | None = None
    while asyncio.get_running_loop().time() < deadline:
        try:
            remaining_seconds = max(deadline - asyncio.get_running_loop().time(), 0.1)
            return await playwright.chromium.connect_over_cdp(
                endpoint,
                timeout=min(int(remaining_seconds * 1_000), 5_000),
                is_local=True,
                no_defaults=True,
            )
        except Error as error:
            last_error = error
            await asyncio.sleep(0.25)
    raise RuntimeError(
        "Could not connect to the dedicated browser. Close every Chrome or Edge window "
        "using this project profile, then retry."
    ) from last_error


async def stop_external_browser(launched: ExternalBrowserProcess) -> None:
    if launched.process.returncode is not None:
        return
    try:
        await asyncio.wait_for(launched.process.wait(), timeout=5.0)
    except TimeoutError:
        launched.process.terminate()
        await launched.process.wait()
