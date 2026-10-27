"""The HTML pages and their preview images (SPEC §9, §15.1). Every page is web/index.html
with server-rendered preview tags (og.py) in place of its <title>; the script routes by
path. Serving a page reads only: it binds nothing (SPEC §15.1)."""
import functools
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from borer_api import og, ogimage

INDEX = Path(__file__).resolve().parents[3] / "web" / "index.html"
router = APIRouter(include_in_schema=False)


@functools.cache
def _index() -> str:
    return INDEX.read_text(encoding="utf-8")


def _page(request: Request, meta: dict, private: bool = True) -> HTMLResponse:
    tags = og.head(meta, og.base_url(request), private)
    return HTMLResponse(_index().replace("<title>הבורר</title>", tags, 1))


def _visible(request: Request, case: dict | None) -> tuple[dict | None, list[dict]]:
    """(case, hearings) if the case can be shown, else (None, [])."""
    if case is None or case["hidden_at"] is not None:
        return None, []
    return request.app.state.store.snapshot(case["id"])


def _teaser_case(request: Request, token: str) -> dict | None:
    found = request.app.state.store.by_token(token)
    return found[0] if found and found[1] == "B" else None


@router.get("/")
@router.get("/how")
def site_page(request: Request):
    return _page(request, og.site(), private=False)


@router.get("/a/{token}")
def a_page(request: Request, token: str):
    return _page(request, og.site())  # A's link is personal: its preview says nothing


@router.get("/b/{token}")
def b_page(request: Request, token: str):
    case, _ = _visible(request, _teaser_case(request, token))
    return _page(request, og.teaser(case) if case else og.site())


@router.get("/c/{cid}")
def c_page(request: Request, cid: str):
    case, hearings = _visible(request, request.app.state.store.case(cid))
    return _page(request, og.card(case, hearings) if case else og.site())


def _png(meta: dict) -> Response:
    return Response(ogimage.png(meta["lines"]), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=300"})


@router.get("/og/site.png")
def site_image():
    return _png(og.site())


@router.get("/og/t/{cid}.png")
def teaser_image(request: Request, cid: str):
    case, _ = _visible(request, request.app.state.store.case(cid))
    return _png(og.teaser(case) if case else og.site())


@router.get("/og/c/{cid}.png")
def card_image(request: Request, cid: str):
    case, hearings = _visible(request, request.app.state.store.case(cid))
    return _png(og.card(case, hearings) if case else og.site())
