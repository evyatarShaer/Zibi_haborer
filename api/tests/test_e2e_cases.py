"""More flows in headless Chrome at 360 px (P2B-8): the 3-hearing appeal chain seen from
both phones, a hearing that ends in error, closed links and A's own device on B's link,
B bound to the browser that submits, and the report button
(and "send the verdict" counted once). Run: uv run pytest -m chrome."""
import time

from e2ekit import (BASE, CLOSED, ENTERS, HEADLINE, TEXT_A, b_writes, get, link_in, open_case,
                    pytestmark, see_story_then)  # noqa: F401 - pytestmark

CHAIN = "פסק דין ← ערעור התקבל ← ערעור נדחה"


def test_appeal_chain_of_three(rig):
    sim, _, browser = rig
    a, b = browser.page(), browser.page()
    url_a, link_b = open_case(a)
    sim.script = [("win", "A"), ("win", "B"), ("win", "B")]
    b_writes(b, link_b)
    see_story_then(b, HEADLINE[("win", "A")])
    a.wait_text(HEADLINE[("win", "A")], 25)  # A's page was open: it followed along
    b.click("button.appeal")  # B appeals and watches it live
    see_story_then(b, "הערעור של יוסי התקבל!", first="ערעור של יוסי!")
    assert not b.attr("button.appeal", "class")  # B's one appeal is used
    a.wait_text("הערעור של יוסי התקבל!", 25)  # A's open page replayed it on its own
    b.goto("about:blank")  # B is away during A's appeal
    a.click("button.appeal")
    see_story_then(a, "הערעור של דנה נדחה", first="ערעור של דנה!")
    assert CHAIN in a.text() and "הפסק סופי" in a.text() and not a.attr("button.appeal", "class")
    b.goto(link_b)  # B reopens: the third verdict is replayed once
    see_story_then(b, "הערעור של דנה נדחה", first="ערעור של דנה!")
    assert CHAIN in b.text() and not b.attr("button.appeal", "class")
    c = browser.page()
    c.goto(link_in(b.attr("a.share", "href"), "c"))
    c.wait_text(HEADLINE[("win", "B")])
    assert CHAIN in c.text() and c.fits()


def test_failed_hearing_ends_in_error(rig):
    sim, _, browser = rig
    a, b = browser.page(), browser.page()
    url_a, link_b = open_case(a)
    sim.script = ["raise"] * 3
    b_writes(b, link_b)
    b.wait_text("השופט התעלף באמצע הדיון", 25)
    a.wait_text("השופט התעלף באמצע הדיון", 10)
    assert b.attr("a.button.primary", "href") == "/" and b.fits()


def test_closed_taken_and_own_links(rig):
    _, _, browser = rig
    a, other = browser.page(), browser.page()
    url_a, link_b = open_case(a)
    for page, url in ((other, BASE + "/a/nope"), (other, BASE + "/b/nope"), (other, BASE + "/c/nope")):
        page.goto(url)
        page.wait_text(CLOSED)
        assert page.attr("a.button.primary", "href") == "/" and page.fits()
    assert get(link_b) == 200  # a preview crawler's GET (no script) does not claim B
    a.goto(link_b)
    a.wait_text("זה הקישור של הצד השני")  # A's device is never B


def test_open_in_one_browser_submit_from_another(rig):
    """WhatsApp's in-app browser → Chrome: B is the browser that submits (SPEC §15.1)."""
    _, _, browser = rig
    a, inapp, chrome, late = browser.page(), browser.page(), browser.page(), browser.page()
    url_a, link_b = open_case(a)
    inapp.goto(link_b)
    inapp.wait("!!document.querySelector('[name=text_b]')")  # opened, not bound
    b_writes(chrome, link_b)
    see_story_then(chrome, HEADLINE[("win", "A")])
    inapp.wait_text("התיק כבר בטיפול", 10)  # its open page notices on the next poll
    late.goto(link_b)
    late.wait_text("התיק כבר בטיפול")
    chrome.goto(link_b)  # the submitting browser stays B
    chrome.wait_text(HEADLINE[("win", "A")])


def _wait_shared(store, cid: str, timeout: float = 10) -> None:
    end = time.time() + timeout
    while store.case(cid)["shared_at"] is None:
        assert time.time() < end, "the share tap never reached the server"
        time.sleep(0.1)
    shared = {r["event"]: r["count"] for r in store.counters()}.get("cases_shared")
    time.sleep(1)  # the second tap has landed by now
    assert {r["event"]: r["count"] for r in store.counters()}.get("cases_shared") == shared


def test_report_hides_the_case(rig):
    sim, _, browser = rig
    a, b, c = browser.page(), browser.page(), browser.page()
    url_a, link_b = open_case(a)
    b_writes(b, link_b)
    see_story_then(b, HEADLINE[("win", "A")])
    b.click("a.share")  # "send the verdict" (twice): the case counts as shared once
    b.click("a.share")
    cid = link_in(b.attr("a.share", "href"), "c").rsplit("/", 1)[1]
    _wait_shared(browser.store, cid)
    c.goto(link_in(b.attr("a.share", "href"), "c"))
    c.wait_text(HEADLINE[("win", "A")])
    c.click("button.report")
    c.wait_text("בטוח?")  # two taps
    c.click("button.report")
    c.wait_text(CLOSED)
    for page, url in ((a, url_a), (b, link_b)):
        page.goto(url)
        page.wait_text(CLOSED)
    assert ENTERS not in b.text()


def test_how_it_works_page(rig):
    _, _, browser = rig
    p = browser.page()
    p.goto(BASE + "/")
    p.click("footer a[href='/how']")
    p.wait_text("קרדיטים")
    assert p.js("document.querySelectorAll('.credits li').length") == 7
    assert p.js("document.querySelectorAll('.credits a[href^=\"https://doi.org/\"]').length") == 7
    assert "CC BY-NC" in p.text() and p.fits()


def test_no_show_b_link_shows_only_the_public_card(rig):
    """Nobody is B after a no-show: B's link must not show A's argument (SPEC §15.1)."""
    sim, clock, browser = rig
    a, b = browser.page(), browser.page()
    url_a, link_b = open_case(a)
    sim.script = [("win", "A")]
    clock.offset += 3 * 3600
    try:
        a.wait_text("הצד השני לא התייצב לדיון", 30)
        b.goto(link_b)
        b.wait_text("הצד השני לא התייצב לדיון")
        assert TEXT_A not in b.text() and "דנה נגד יוסי" in b.text() and b.fits()
        assert b.attr("a.button.primary", "href") == "/" and not b.attr("button.appeal", "class")
        assert not b.attr("[name=text_b]", "name") and not b.attr("button.brain-toggle", "class")
    finally:
        clock.offset = 0
