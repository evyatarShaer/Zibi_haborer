"""Verdict wording (borer_api.verdicts): SPEC §7 headlines, the §8 no-show headlines and
the history line, in one place for the API, the pages and the link previews."""
import pytest

from borer_api import verdicts
from fake import ROOT

CASE = {"name_a": "דנה", "name_b": "יוסי", "text_b": "טענה"}


def spec_headlines():
    table = (ROOT / "docs" / "SPEC.md").read_text().split("## 7. Outcomes")[1].split("## 8.")[0]
    rows = [r.split("|") for r in table.splitlines() if r.startswith("| ") and not r.startswith("| Outcome")]
    return {r[1].strip().split()[0].lower(): r[3].strip() for r in rows}


def h(outcome="win", winner="A", status="decided"):
    return {"outcome": outcome, "winner": winner, "status": status}


@pytest.mark.parametrize("row, outcome, winner", [
    ("win", "win", "A"), ("dithered", "dithered", "B"), ("plain", "tie", None),
    ("froze", "froze", None), ("lunch", "food", None)])
def test_headlines_are_spec_section_7(row, outcome, winner):
    name = {"A": "דנה", "B": "יוסי"}.get(winner, "")
    assert verdicts.headline(CASE, h(outcome, winner)) == spec_headlines()[row].replace("{name}", name)


@pytest.mark.parametrize("outcome, winner, line", [
    ("win", "A", "הצד השני לא התייצב לדיון"), ("win", "B", "הזבוב העדיף מים"),
    ("dithered", "B", "הזבוב העדיף מים"), ("tie", None, "הצד השני לא התייצב לדיון"),
    ("froze", None, "הצד השני לא התייצב לדיון")])
def test_no_show_headlines(outcome, winner, line):
    assert verdicts.headline(CASE | {"text_b": None}, h(outcome, winner)) == line


def test_history_line_and_accepted():
    chain = [h("win", "A"), h("win", "B"), h("win", "B")]
    assert verdicts.history_line(chain[:1]) is None
    assert verdicts.history_line(chain) == "פסק דין ← ערעור התקבל ← ערעור נדחה"
    assert verdicts.history_line(chain[:2] + [h(status="running")]) == "פסק דין ← ערעור התקבל"
    assert verdicts.accepted(h("tie", None), h("froze", None)) is False  # no winner both times
    assert verdicts.accepted(h(), h(status="failed")) is None
