"""API response shapes and Hebrew messages. Fields are listed explicitly, so nothing stored
leaks by accident: no letter-level data (SPEC §2.3), no `text_a` for B while the case
waits (§15.2), no arguments, mood or brain on the public card (§9)."""
from fastapi.responses import JSONResponse

from borer_api import tokens, verdicts

CLOSED = "התיק נסגר. אפשר לפתוח תיק חדש"
TAKEN = "התיק כבר בטיפול"
OWN_LINK = "זה הקישור של הצד השני. שלחו אותו אליו"
LIMIT = "הזבוב שמע מספיק תיקים מכם היום. נסו שוב מחר"
LATE = "הזמן להגשת הטענה עבר"
SUBMITTED = "הטענה כבר הוגשה"
NOT_DECIDED = "הזבוב עוד לא פסק בתיק הזה"
APPEALED = "כבר ערערת בתיק הזה"
FINAL = "הפסק סופי. אין עוד ערעורים בתיק הזה"
APPEAL_LATE = "עברו 3 שעות מפסק הדין. הפסק סופי"
FAILED = "משהו השתבש במוח של הזבוב והתיק לא נשמע. אפשר לפתוח תיק חדש"

NUDGE_AFTER_S = 3600          # A's "nudge again" button (SPEC §3.2)
APPEAL_WINDOW_S = 3 * 3600    # appeals within 3 h of the latest verdict (§15.4)
MAX_HEARINGS = 3
# The lab view's fields (SPEC §15.7): MN9 curves and the run's identity, no taste classes.
BRAIN = ("bin_ms", "mn9_hz", "mood", "seed", "sim_version", "platform")


def error(message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


def closed() -> JSONResponse:
    """The one answer for a wrong token, an expired, deleted or hidden case (§15.8)."""
    return error(CLOSED, 404)


def appeal_refused(case: dict, hearings: list[dict], side: str, now: float) -> str | None:
    """Why `side` cannot appeal now (Hebrew), or None if it can (SPEC §15.4). After a
    no-show only A can get here: B's link has no personal page (routes._party)."""
    if case["status"] not in ("decided", "no_show"):
        return NOT_DECIDED
    if any(h["appealed_by"] == side for h in hearings):
        return APPEALED
    if len(hearings) >= MAX_HEARINGS:
        return FINAL
    if now > hearings[-1]["decided_at"] + APPEAL_WINDOW_S:
        return APPEAL_LATE
    return None


def hearing(h: dict, prev: dict | None, case: dict, public: bool = False) -> dict:
    """One hearing of the history; the verdict fields (headline included) appear once it
    is decided."""
    out = {k: h[k] for k in ("n", "appealed_by", "status")}
    if not public:
        out |= {"wait_h": h["wait_h"], "mood": {"hunger": h["hunger"], "arousal": h["arousal"]}}
    if h["status"] == "decided":
        out |= {"outcome": h["outcome"], "winner": h["winner"],
                "winner_name": verdicts.winner_name(case, h),
                "headline": verdicts.headline(case, h)}
        if not public:
            out["appetite"] = {"A": h["metrics"]["A"], "B": h["metrics"]["B"]}
        if (a := verdicts.accepted(h, prev)) is not None:
            out["accepted"] = a
    return out


def hearing_list(case: dict, hearings: list[dict], public: bool = False) -> list[dict]:
    return [hearing(h, hearings[i - 1] if i else None, case, public) for i, h in enumerate(hearings)]


def _common(case: dict, hearings: list[dict], public: bool) -> dict:
    return {k: case[k] for k in ("id", "status", "topic", "name_a", "name_b")} | {
        "no_show": case["status"] not in ("waiting", "error") and case["text_b"] is None,
        "error_message": FAILED if case["status"] == "error" else None,
        "hearings": hearing_list(case, hearings, public),
        "history": verdicts.history_line(hearings)}


def public(case: dict, hearings: list[dict]) -> dict:
    """The public share card's data: topic, names, verdicts and their history."""
    return _common(case, hearings, public=True)


def personal(case: dict, side: str, token: str, hearings: list[dict], now: float) -> dict:
    """A side's personal page. `token` is the link's own token (A's rebuilds B's link)."""
    waiting = case["status"] == "waiting"
    refused = appeal_refused(case, hearings, side, now)
    out = _common(case, hearings, public=False) | {
        "you": side, "text_b": case["text_b"],
        "text_a": None if side == "B" and waiting else case["text_a"],
        "deadline_in_s": max(0.0, case["deadline_at"] - now),
        "can_appeal": refused is None,
        "appeal_closes_in_s": None if refused else hearings[-1]["decided_at"] + APPEAL_WINDOW_S - now}
    if side == "A" and waiting:
        out |= {"link_b": f"/b/{tokens.side_b(token)}",
                "nudge": now >= case["created_at"] + NUDGE_AFTER_S}
    return out


def brain(b: dict) -> dict:
    return {k: b[k] for k in BRAIN}
