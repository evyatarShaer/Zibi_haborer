"""Case API (SPEC §3, §15; P2B-6) under /api. Personal links: /a/{token}, /b/{token};
the public card: /c/{case id}. Every closed case (wrong token, expired, deleted, hidden)
gets the same 404. B's link is bound to the first device whose page calls
POST /api/b/{token}/open (a device cookie); a plain GET never binds it."""
import sqlite3

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from borer_api import tokens, validate, views
from borer_api.cases import Busy, Closed, Limited
from borer_api.court import BUSY, new_seed

DEVICE, DEVICE_MAX_AGE = "borer_device", 30 * 24 * 3600
PER_DAY = 20  # new cases per IP per day (SPEC §15.5)

router = APIRouter(prefix="/api")


class NewCase(BaseModel):
    topic: str | None = None
    name_a: str
    name_b: str
    text_a: str


class Argument(BaseModel):
    text_b: str


def _with_device(request: Request, response: JSONResponse) -> JSONResponse:
    """Give the browser a device cookie if it has none (request.state.device holds it)."""
    if DEVICE not in request.cookies:
        response.set_cookie(DEVICE, request.state.device, max_age=DEVICE_MAX_AGE,
                            httponly=True, samesite="lax")
    return response


def _device(request: Request) -> str:
    request.state.device = request.cookies.get(DEVICE) or tokens.new()
    return request.state.device


def _link(request: Request, side: str, token: str) -> dict | None:
    """The open, visible case behind a personal link of `side` ("a"/"b"), or None."""
    found = request.app.state.store.by_token(token)
    ok = found is not None and found[1] == side.upper() and found[0]["hidden_at"] is None
    return found[0] if ok else None


def _party(request: Request, side: str, token: str) -> tuple[dict | None, JSONResponse | None]:
    """(case, None) for a personal link of `side`, else (None, the error).
    B's link answers only the device bound to it."""
    case, device = _link(request, side, token), request.cookies.get(DEVICE)
    if case is None:
        return None, views.closed()
    if side == "b" and (device is None or tokens.digest(device) != case["b_device_hash"]):
        return None, views.error(views.TAKEN, 403)
    return case, None


def _view(request: Request, case: dict, side: str, token: str, status: int = 200):
    """The personal page of `side`, read fresh (after any write of this request)."""
    store = request.app.state.store
    case, hearings = store.snapshot(case["id"])
    return JSONResponse(views.personal(case, side.upper(), token, hearings, store.clock()),
                        status_code=status)


@router.post("/case", status_code=201)
def open_case(req: NewCase, request: Request):
    topic = (req.topic or "").strip() or None
    names, text_a = {"a": req.name_a.strip(), "b": req.name_b.strip()}, req.text_a.strip()
    if errors := validate.problems(topic, names, {"a": text_a}):
        return JSONResponse({"errors": errors}, status_code=422)
    try:
        c = request.app.state.store.open(topic, names["a"], names["b"], text_a,
                                         ip=request.client.host, device=_device(request),
                                         per_day=PER_DAY)
    except Limited:
        return views.error(views.LIMIT, 429)
    return _with_device(request, JSONResponse(
        {"case_id": c["id"], "link_a": f"/a/{c['token_a']}", "link_b": f"/b/{c['token_b']}"},
        status_code=201))


@router.get("/a/{token}")
def a_view(token: str, request: Request):
    case, err = _party(request, "a", token)
    return err or _view(request, case, "a", token)


@router.post("/b/{token}/open")
def b_open(token: str, request: Request):
    """The page's first call on B's link: bind this device as B if B is still free."""
    store, case = request.app.state.store, _link(request, "b", token)
    if case is None:
        return views.closed()
    bound = store.claim_b(case["id"], _device(request))
    if bound == "A":
        return _with_device(request, views.error(views.OWN_LINK, 409))
    if bound is None:
        return _with_device(request, views.error(views.TAKEN, 403))
    return _with_device(request, _view(request, case, "b", token))


@router.get("/b/{token}")
def b_view(token: str, request: Request):
    case, err = _party(request, "b", token)
    return err or _view(request, case, "b", token)


@router.post("/b/{token}/submit")
def b_submit(token: str, req: Argument, request: Request):
    case, err = _party(request, "b", token)
    if err:
        return err
    text_b, store = req.text_b.strip(), request.app.state.store
    if errors := validate.problems(None, {}, {"b": text_b}):
        return JSONResponse({"errors": errors}, status_code=422)
    try:
        store.submit_b(case["id"], text_b, new_seed())
    except Closed:
        late = store.clock() >= case["deadline_at"]
        return views.error(views.LATE if late else views.SUBMITTED, 409)
    except Busy:
        return views.error(BUSY, 503)
    request.app.state.court.wake()
    return _view(request, case, "b", token)


@router.post("/{side}/{token}/appeal")
def appeal(side: str, token: str, request: Request):
    case, err = _party(request, side, token)
    if err:
        return err
    store, s = request.app.state.store, side.upper()
    if refused := views.appeal_refused(case, store.hearings(case["id"]), s, store.clock()):
        return views.error(refused, 409)
    try:
        store.appeal(case["id"], s, new_seed())
    except (Closed, sqlite3.IntegrityError):  # another appeal won the race
        return views.error(views.NOT_DECIDED, 409)
    except Busy:
        return views.error(BUSY, 503)
    request.app.state.court.wake()
    return _view(request, case, side, token, status=201)


@router.get("/{side}/{token}/brain/{n}")
def brain(side: str, token: str, n: int, request: Request):
    case, err = _party(request, side, token)
    if err:
        return err
    h = next((h for h in request.app.state.store.hearings(case["id"]) if h["n"] == n), None)
    if h is None:
        return views.closed()
    if h["status"] != "decided":
        return views.error(views.NOT_DECIDED, 409)
    return views.brain(h["brain"])


@router.get("/c/{cid}")
def public_card(cid: str, request: Request):
    case, hearings = request.app.state.store.snapshot(cid)
    if case is None or case["hidden_at"] is not None:
        return views.closed()
    return views.public(case, hearings)
