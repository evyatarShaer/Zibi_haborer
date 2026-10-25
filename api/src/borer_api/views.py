"""API response shapes. Fields are listed explicitly, so nothing stored leaks by accident
(SPEC §2.3: no letter-level data; the brain summary is group-level by construction)."""
from fastapi.responses import JSONResponse

NOT_FOUND = "התיק לא נמצא (אולי עברו 7 ימים והוא נמחק)"
NOT_DECIDED = "הזבוב עוד לא פסק בתיק הזה"
APPEALED = "כבר הוגש ערעור בתיק הזה"
APPEAL_OF_APPEAL = "אי אפשר לערער על ערעור. הפסק סופי"
BASE = ("id", "status", "topic", "name_a", "name_b", "text_a", "text_b", "appeal_of")


def not_found() -> JSONResponse:
    return JSONResponse({"error": NOT_FOUND}, status_code=404)


def appeal_refused(h: dict, appeal: dict | None) -> str | None:
    """Why `h` cannot be appealed (Hebrew), or None if it can (SPEC §14.5)."""
    if h["appeal_of"] is not None:
        return APPEAL_OF_APPEAL
    if appeal is not None:
        return APPEALED
    if h["status"] != "decided":
        return NOT_DECIDED
    return None


def hearing(h: dict, appeal: dict | None, original: dict | None) -> dict:
    """A hearing as the page sees it; the verdict fields appear once it is decided.
    `appeal` is the appeal filed against it, `original` the hearing it appeals."""
    out = {k: h[k] for k in BASE} | {"mood": {"hunger": h["hunger"], "arousal": h["arousal"]}}
    out["can_appeal"] = appeal_refused(h, appeal) is None
    out["appeal_id"] = appeal["id"] if appeal else None
    if h["status"] == "decided":
        w = h["winner"]
        out |= {"outcome": h["outcome"], "winner": w,
                "winner_name": h[f"name_{w.lower()}"] if w else None,
                "appetite": {"A": h["metrics"]["A"], "B": h["metrics"]["B"]}}
        if original is not None and original["status"] == "decided":
            # The stored winner is None for outcomes that name no side, so a non-win
            # counts as "no winner" in the comparison.
            out["appeal_accepted"] = w != original["winner"]
    return out
