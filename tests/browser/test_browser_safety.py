import pytest

from youtube_knowledge_manager.browser.selectors import Selectors
from youtube_knowledge_manager.browser.session import BrowserSession, ManualInterventionRequired
from youtube_knowledge_manager.settings import Settings


class Locator:
    def __init__(self, count: int) -> None:
        self.value = count

    async def count(self) -> int:
        return self.value


class Page:
    def __init__(self, url: str, active_selector: str | None = None) -> None:
        self.url = url
        self.active_selector = active_selector

    def locator(self, selector: str) -> Locator:
        return Locator(1 if selector == self.active_selector else 0)


@pytest.mark.browser
@pytest.mark.asyncio
async def test_security_url_stops_automation() -> None:
    session = BrowserSession(Settings())
    session.page = Page("https://accounts.google.com/challenge/")  # type: ignore[assignment]

    with pytest.raises(ManualInterventionRequired, match="security page"):
        await session.ensure_safe_page()


@pytest.mark.browser
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("selector", "label"),
    [
        (Selectors.CAPTCHA, "CAPTCHA"),
        (Selectors.CONSENT_DIALOG, "consent dialog"),
        (Selectors.SECURITY_PROMPT, "security prompt"),
        (Selectors.LOGIN_FORM, "login prompt"),
    ],
)
async def test_page_interruption_selectors_stop_automation(selector: str, label: str) -> None:
    session = BrowserSession(Settings())
    session.page = Page("https://www.youtube.com/", selector)  # type: ignore[assignment]

    with pytest.raises(ManualInterventionRequired, match=label):
        await session.ensure_safe_page()


@pytest.mark.browser
@pytest.mark.asyncio
async def test_safe_page_continues() -> None:
    session = BrowserSession(Settings())
    session.page = Page("https://www.youtube.com/")  # type: ignore[assignment]

    await session.ensure_safe_page()
