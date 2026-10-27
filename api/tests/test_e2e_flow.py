"""The two-link flow in headless Chrome at 360 px (P2B-8): every outcome, A's replay, the
public card; the no-show (plain water) with A's appeal. Run: uv run pytest -m chrome."""
import pytest

from e2ekit import (BASE, CLOSED, HEADLINE, TEXT_A, TEXT_B, WATER, b_writes, link_in,
                    open_case, pytestmark, see_story_then)  # noqa: F401 - pytestmark

OUTCOMES = list(HEADLINE)[1:]  # win B, dithered, tie, froze, lunch break (+ win A in the chain)


@pytest.mark.parametrize("outcome", OUTCOMES)
def test_every_outcome_live_for_b_replay_for_a(rig, outcome):
    sim, _, browser = rig
    a, b = browser.page(), browser.page()
    url_a, link_b = open_case(a, topic="פיצה" if outcome[0] != "tie" else None)
    a.goto("about:blank")  # A is away while B writes
    sim.script = [outcome]
    b_writes(b, link_b)
    see_story_then(b, HEADLINE[outcome])  # live
    assert TEXT_A in b.text() and TEXT_B in b.text()  # both arguments after the verdict
    assert ("התיק: פיצה" in b.text()) == (outcome[0] != "tie")
    assert b.attr("button.appeal", "class")  # B may appeal
    public = link_in(b.attr("a.share", "href"), "c")
    a.goto(url_a)
    see_story_then(a, HEADLINE[outcome])  # replayed from stored data
    a.goto(url_a)
    a.wait_text(HEADLINE[outcome], 5)
    assert "השופט נכנס" not in a.text()  # seen once: no second replay
    c = browser.page()
    c.goto(public)
    c.wait_text(HEADLINE[outcome])
    assert "דנה נגד יוסי" in c.text() and TEXT_A not in c.text() and TEXT_B not in c.text()
    assert c.fits()


def test_no_show_water_then_a_appeals(rig):
    sim, clock, browser = rig
    a, b = browser.page(), browser.page()
    url_a, link_b = open_case(a)
    clock.offset += 3600
    a.wait("!document.querySelector('a.nudge').hidden", 10)  # the nudge from 1 h
    assert link_b.split("/")[-1] in link_in(a.attr("a.nudge", "href"), "b")
    sim.script = [("win", "B"), ("win", "A")]
    clock.offset += 2 * 3600  # the 3 h deadline: plain water
    see_story_then(a, "הזבוב העדיף מים", first=WATER)
    assert "כוס מים" in a.text()
    a.click("button.appeal")
    see_story_then(a, "הצד השני לא התייצב לדיון", first="ערעור של דנה!")
    assert "הערעור של דנה התקבל!" in a.text() and not a.attr("button.appeal", "class")
    b.goto(link_b)  # B comes late: the verdicts, no appeal, no form
    b.wait_text("הצד השני לא התייצב לדיון", 25)
    assert not b.attr("button.appeal", "class") and not b.attr("[name=text_b]", "name")
    clock.offset = 0
    assert CLOSED not in b.text() and BASE in b.attr("a.share", "href").replace("%3A", ":").replace("%2F", "/")
