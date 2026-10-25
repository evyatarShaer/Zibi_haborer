"""API response shapes. Fields are listed explicitly, so nothing stored leaks by accident
(SPEC §2.3: no letter-level data; the brain summary is group-level by construction)."""
from fastapi.responses import JSONResponse

NOT_FOUND = "התיק לא נמצא (אולי עברו 7 ימים והוא נמחק)"
NOT_DECIDED = "הזבוב עוד לא פסק בתיק הזה"
BASE = ("id", "status", "topic", "name_a", "name_b", "text_a", "text_b", "appeal_of")


def not_found() -> JSONResponse:
    return JSONResponse({"error": NOT_FOUND}, status_code=404)


def hearing(h: dict, has_appeal: bool) -> dict:
    """A hearing as the page sees it; the verdict fields appear once it is decided."""
    out = {k: h[k] for k in BASE} | {"mood": {"hunger": h["hunger"], "arousal": h["arousal"]}}
    out["can_appeal"] = h["status"] == "decided" and h["appeal_of"] is None and not has_appeal
    if h["status"] == "decided":
        w = h["winner"]
        out |= {"outcome": h["outcome"], "winner": w,
                "winner_name": h[f"name_{w.lower()}"] if w else None,
                "appetite": {"A": h["metrics"]["A"], "B": h["metrics"]["B"]}}
    return out
