"""Verdict wording (SPEC §7, §8, §15.4): the one copy of the headlines and the history
line. The API sends them with each case (views.py), the pages show them as sent, and the
link previews draw them (og.py), so the three never disagree."""

HEADLINES = {  # SPEC §7 (decided 2026-10-25)
    "win": "פסק הדין: הצדק עם {name}",
    "dithered": "אחרי התלבטות קשה... הצדק עם {name}",
    "tie": "תיקו. הזבוב לא השתכנע מאף אחד",
    "froze": "הזבוב קפא. התיק הזה גדול עליו",
    "food": "הבורר יצא להפסקת צהריים. הדיון נדחה",
}
PREFERRED_WATER = "הזבוב העדיף מים"  # SPEC §8: a no-show that water wins
NO_SHOW = "הצד השני לא התייצב לדיון"   # SPEC §8: any other no-show verdict
STEPS = {None: "פסק דין", True: "ערעור התקבל", False: "ערעור נדחה"}


def winner_name(case: dict, h: dict) -> str | None:
    return case[f"name_{h['winner'].lower()}"] if h["winner"] else None


def headline(case: dict, h: dict) -> str:
    """The headline of a decided hearing; a no-show (B never wrote) has its own."""
    if case["text_b"] is None:
        return PREFERRED_WATER if h["winner"] == "B" else NO_SHOW
    return HEADLINES[h["outcome"]].format(name=winner_name(case, h))


def accepted(h: dict, prev: dict | None) -> bool | None:
    """An appeal is accepted when its winner differs from the previous verdict's (no
    winner = None); None for the first verdict or an undecided previous hearing."""
    if prev is None or prev["status"] != "decided":
        return None
    return h["winner"] != prev["winner"]


def history_line(hearings: list[dict]) -> str | None:
    """verdict ← appeal accepted ← appeal rejected (decided hearings), from two on."""
    steps = [STEPS[accepted(h, hearings[i - 1] if i else None)]
             for i, h in enumerate(hearings) if h["status"] == "decided"]
    return " ← ".join(steps) if len(steps) > 1 else None


def final(case: dict, hearings: list[dict]) -> dict | None:
    """The latest decided hearing, if the case is not in the middle of another one."""
    decided = [h for h in hearings if h["status"] == "decided"]
    return decided[-1] if decided and case["status"] in ("decided", "no_show") else None
