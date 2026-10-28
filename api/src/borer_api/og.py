"""Link previews (SPEC §9): the Open Graph tags each page is served with and the lines its
image draws. WhatsApp's crawler runs no script, so this is all it sees.

- B's link: the **teaser**, the fly and the topic only, never a verdict.
- The public card: topic, names, the final verdict and its history.
- Everything else (the start page, /how, A's personal link, a closed case): the site.
No argument, mood or brain data appears in any tag or image.
"""
import html
import os

from borer_api import verdicts

SITE_TITLE = "הבורר"
SITE_TEXT = "יש ויכוח? זבוב אמיתי יכריע. 140 אלף נוירונים, בלי AI."
TEASER_TEXT = "הוגשה נגדך תביעה. יש לך 3 שעות להתגונן."
NOT_DECIDED = "הזבוב עוד לא פסק בתיק הזה"


def site() -> dict:
    return {"title": SITE_TITLE, "text": SITE_TEXT, "image": "/og/site.png",
            "lines": [("headline", "שני צדדים, זבוב אחד מכריע"), ("note", "בלי AI. רק מוח של זבוב.")]}


def teaser(case: dict) -> dict:
    topic = f"התיק: {case['topic']}" if case["topic"] else "הוגשה נגדך תביעה"
    return {"title": f"{SITE_TITLE} · {topic}", "text": TEASER_TEXT,
            "image": f"/og/t/{case['id']}.png", "lines": [("headline", topic), ("note", TEASER_TEXT)]}


def card(case: dict, hearings: list[dict]) -> dict:
    final = verdicts.final(case, hearings)
    head = verdicts.headline(case, final) if final else NOT_DECIDED
    topic = f"התיק: {case['topic']}" if case["topic"] else None
    names = f"{case['name_a']} נגד {case['name_b']}"
    history = verdicts.history_line(hearings) if final else None
    lines = [("topic", topic), ("names", names), ("headline", head),
             ("history", history and history.replace("←", "·"))]  # Heebo has no arrows
    return {"title": head, "text": " · ".join(t for t in (topic, names, history) if t),
            "image": f"/og/c/{case['id']}.png?v={len(hearings)}{case['status']}",
            "lines": [(role, text) for role, text in lines if text]}


def base_url(request) -> str:
    """Absolute site address for og:image: BORER_PUBLIC_URL on the server, else the
    address the request came to (a proxy's X-Forwarded-Host honoured; uvicorn already
    takes the scheme from a local proxy's X-Forwarded-Proto)."""
    if env := os.environ.get("BORER_PUBLIC_URL"):
        return env.rstrip("/")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    return f"{request.url.scheme}://{host}"


def head(meta: dict, base: str, private: bool) -> str:
    """The <title> and meta tags; `private` pages also ask not to be indexed."""
    e = lambda s: html.escape(s, quote=True)  # noqa: E731
    tags = [f"<title>{e(meta['title'])}</title>",
            f'<meta property="og:title" content="{e(meta["title"])}">',
            f'<meta property="og:description" content="{e(meta["text"])}">',
            f'<meta name="description" content="{e(meta["text"])}">',
            f'<meta property="og:image" content="{e(base + meta["image"])}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            '<meta property="og:type" content="website">', '<meta property="og:locale" content="he_IL">',
            '<meta name="twitter:card" content="summary_large_image">']
    if private:
        tags.append('<meta name="robots" content="noindex">')
    return "\n".join(tags)
