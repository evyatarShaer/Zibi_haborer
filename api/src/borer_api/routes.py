"""Case API (SPEC §3, §15; P2B-6) under /api. Personal links: /a/{token}, /b/{token};
the public card: /c/{case id}. Every closed case (wrong token, expired, deleted, hidden)
gets the same 404. Before B submits, any device but A's may open B's link (and switch
browsers); the device that submits B's argument becomes B (device cookie), and later
other devices get "התיק כבר בטיפול" (SPEC §15.1)."""
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
    """(case, None) for a personal link of `side`, else (None, the error). B's link never
    answers A's device, and once B has submitted, only the device that did."""
    case, device = _link(request, side, token), request.cookies.get(DEVICE)
    if case is None:
        return None, views.closed()
    if side == "b":
        d = device and tokens.digest(device)
        if d is not None and d == case["a_device_hash"]:
            return None, views.error(views.OWN_LINK, 409)
        if case["b_device_hash"] is not None and d != case["b_device_hash"]:
            return None, views.error(views.TAKEN, 403)
        if _no_b(case):  # nobody wrote for B: nothing personal behind B's link
            return None, views.error(views.LATE, 409)
    return case, None


def _no_b(case: dict) -> bool:
    """B never submitted and the deadline hearing was filed (a no-show)."""
    return case["status"] != "waiting" and case["text_b"] is None


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


@router.get("/b/{token}")
def b_view(token: str, request: Request):
    """B's page; gives the browser its device cookie (needed to submit and come back)."""
    device = _device(request)
    found = _link(request, "b", token)
    if found and _no_b(found) and tokens.digest(device) != found["a_device_hash"]:
        # After a no-show nobody is B: the link shows only the public card (SPEC §15.1).
        case, hearings = request.app.state.store.snapshot(found["id"])
        return _with_device(request, JSONResponse({"public_only": views.public(case, hearings)}))
    case, err = _party(request, "b", token)
    return _with_device(request, err or _view(request, case, "b", token))


@router.post("/b/{token}/submit")
def b_submit(token: str, req: Argument, request: Request):
    case, err = _party(request, "b", token)
    if err:
        return err
    text_b, store = req.text_b.strip(), request.app.state.store
    if errors := validate.problems(None, {}, {"b": text_b}):
        return JSONResponse({"errors": errors}, status_code=422)
    try:
        store.submit_b(case["id"], text_b, new_seed(), device=_device(request))
    except Closed:
        late = store.clock() >= case["deadline_at"]
        return views.error(views.LATE if late else views.SUBMITTED, 409)
    except Busy:
        return views.error(BUSY, 503)
    request.app.state.court.wake()
    return _with_device(request, _view(request, case, "b", token))


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


@router.post("/c/{cid}/report")
def report(cid: str, request: Request):
    """The public card's report button: the case is hidden at once (SPEC §15.5)."""
    if not request.app.state.store.report(cid):
        return views.closed()
    return {"hidden": True}
