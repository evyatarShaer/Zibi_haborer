"""Page-test kit (P2B-8): the real app and page on 127.0.0.1:8077 with a scripted sim and
a clock that can jump ahead (the `rig` fixture, conftest.py), driven in headless Chrome
(cdp.py), one browser context per device."""
import re
import time
import urllib.parse
import urllib.request

import pytest
from cdp import CHROME
from fake import FakeSim

PORT = 8077
BASE = f"http://127.0.0.1:{PORT}"
pytestmark = [pytest.mark.chrome,
              pytest.mark.skipif(not CHROME.exists(), reason="Windows Chrome not found")]
# Page copy the tests look for (web/js/copy.js; SPEC §7, §8).
ENTERS, WATER, CLOSED = "השופט נכנס לאולם", "טועם כוס מים", "התיק נסגר. אפשר לפתוח תיק חדש"
HEADLINE = {("win", "A"): "פסק הדין: הצדק עם דנה", ("win", "B"): "פסק הדין: הצדק עם יוסי",
            ("dithered", "B"): "אחרי התלבטות קשה... הצדק עם יוסי",
            ("tie", None): "תיקו. הזבוב לא השתכנע מאף אחד",
            ("froze", None): "הזבוב קפא. התיק הזה גדול עליו",
            ("food", None): "הבורר יצא להפסקת צהריים. הדיון נדחה"}
TEXT_A, TEXT_B = "פיצה עם אננס זה פשוט טעים", "אננס על פיצה זה פשע נגד האנושות"


class Script(FakeSim):
    """Answers the next scripted (outcome, winner), or raises for "raise"; ~0.3 s each."""

    def __init__(self):
        super().__init__()
        self.script = []

    def __call__(self, *args):
        item = self.script.pop(0) if self.script else ("win", "A")
        if item == "raise":
            self.calls.append(args)
            raise RuntimeError("scripted failure")
        self.outcome, self.winner = item
        time.sleep(0.3)
        return super().__call__(*args)


class Shift:
    """Real time plus an offset the tests move forward (the 3 h deadline)."""

    def __init__(self):
        self.offset = 0.0

    def __call__(self):
        return time.time() + self.offset


def link_in(wa_href: str, kind: str) -> str:
    """The /b/ or /c/ link inside a wa.me share text."""
    text = urllib.parse.unquote(wa_href.split("text=")[1])
    return re.search(rf"https?://\S+/{kind}/[\w-]+", text).group(0)


def open_case(a, topic: str | None = "פיצה") -> tuple[str, str]:
    """A opens a case; returns (A's URL, B's link)."""
    a.goto(BASE + "/")
    for name, value in (("topic", topic or ""), ("name_a", "דנה"), ("name_b", "יוסי"), ("text_a", TEXT_A)):
        a.fill(name, value)
    assert a.fits()
    a.click("form button[type=submit]")
    a.wait("location.pathname.startsWith('/a/')")
    a.wait_text("בית המשפט ממתין לטענה של יוסי")
    assert a.fits() and a.attr("a.nudge", "href") is None  # no nudge before 1 h
    return BASE + a.path(), link_in(a.attr("a.send", "href"), "b")


def b_writes(b, link_b: str, text: str = TEXT_B) -> None:
    b.goto(link_b)
    b.wait("!!document.querySelector('[name=text_b]')")
    assert TEXT_A not in b.text() and b.fits()  # blind
    b.fill("text_b", text)
    b.click("form button[type=submit]")


def see_story_then(page, headline: str, first: str = ENTERS) -> None:
    """The waiting story is told (live or replayed), then the verdict shows."""
    page.wait_text(first, 10)
    assert headline not in page.text() and page.fits()
    page.wait_text(headline, 25)
    assert page.fits()


def get(url: str) -> int:
    try:
        return urllib.request.urlopen(url, timeout=5).status
    except urllib.error.HTTPError as e:
        return e.code
