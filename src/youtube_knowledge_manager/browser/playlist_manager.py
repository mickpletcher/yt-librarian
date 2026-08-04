from __future__ import annotations

from dataclasses import dataclass

from youtube_knowledge_manager.browser.selectors import Selectors
from youtube_knowledge_manager.browser.session import BrowserSession


@dataclass(frozen=True)
class PlaylistAddResult:
    changed: bool
    already_present: bool
    dry_run: bool


class PlaylistManager:
    def __init__(self, browser: BrowserSession) -> None:
        self.browser = browser

    async def add_video(
        self, *, canonical_url: str, playlist_name: str, dry_run: bool = True
    ) -> PlaylistAddResult:
        page = self.browser.require_page()
        await page.goto(canonical_url, wait_until="domcontentloaded")
        await self.browser.ensure_safe_page()
        save_button = page.locator(Selectors.SAVE_BUTTON).first
        await save_button.wait_for(state="visible")
        await save_button.click()
        dialog = page.locator(Selectors.PLAYLIST_DIALOG).last
        await dialog.wait_for(state="visible")
        options = dialog.locator(Selectors.PLAYLIST_OPTION)
        for index in range(await options.count()):
            option = options.nth(index)
            label = (await option.locator(Selectors.PLAYLIST_OPTION_TITLE).inner_text()).strip()
            if label != playlist_name:
                continue
            checkbox = option.locator(Selectors.PLAYLIST_OPTION_CHECKBOX)
            checked = (await checkbox.get_attribute("aria-checked")) == "true"
            if checked:
                await page.keyboard.press("Escape")
                return PlaylistAddResult(changed=False, already_present=True, dry_run=dry_run)
            if dry_run:
                await page.keyboard.press("Escape")
                return PlaylistAddResult(changed=False, already_present=False, dry_run=True)
            await checkbox.click()
            await self.browser.pause_between_actions()
            if (await checkbox.get_attribute("aria-checked")) != "true":
                raise RuntimeError(
                    f"YouTube did not confirm playlist selection for {playlist_name}"
                )
            await page.keyboard.press("Escape")
            return PlaylistAddResult(changed=True, already_present=False, dry_run=False)
        await page.keyboard.press("Escape")
        raise LookupError(f"YouTube playlist not found: {playlist_name}")
