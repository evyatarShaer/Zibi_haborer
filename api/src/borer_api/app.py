"""HaBorer local API (Phase 2A, SPEC §14): FastAPI around borer_sim + SQLite, serving web/.

Run: scripts/run_local.sh. Env: BORER_DB (default api/data/hearings.sqlite3).
create_app(runner=...) takes a fake simulation for tests. Without one, the lifespan starts
the two tasting workers with "forkserver" (each builds its own model, so this threaded
process is never forked) and warms them up. It also starts the 7-day purge loop.
"""
import os
import secrets
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from borer_api import court, validate, views
from borer_api.store import Store, cleanup_loop
from borer_sim import mood

ROOT = Path(__file__).resolve().parents[3]
DB = os.environ.get("BORER_DB", str(ROOT / "api" / "data" / "hearings.sqlite3"))
WARMUP = "בדיקה קצרה של הזבוב לפני הדיון"


class NewHearing(BaseModel):
    topic: str | None = None
    name_a: str
    name_b: str
    text_a: str
    text_b: str


def real_runner():
    """(runner, pool): the product hearing on forkserver workers, warmed up."""
    from borer_sim import hearing
    pool = hearing.workers(method="forkserver")
    hearing.run(pool, WARMUP, WARMUP, 0, ms=100)
    return (lambda a, b, seed: hearing.run(pool, a, b, seed)), pool


def create_app(runner=None, db_path: str = DB, purge_every_s: float = 3600) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        store, pool = Store(db_path), None
        store.fail_unfinished()
        run = runner
        if run is None:
            run, pool = real_runner()
        stop = threading.Event()
        threading.Thread(target=cleanup_loop, args=(store, stop, purge_every_s),
                         name="purge", daemon=True).start()
        app.state.store, app.state.court = store, court.Court(store, run)
        yield
        stop.set()
        app.state.court.close()
        if pool is not None:
            pool.terminate()

    app = FastAPI(title="HaBorer", lifespan=lifespan)

    @app.post("/hearing", status_code=201)
    def new_hearing(req: NewHearing):
        topic = (req.topic or "").strip() or None
        names = {"a": req.name_a.strip(), "b": req.name_b.strip()}
        texts = {"a": req.text_a.strip(), "b": req.text_b.strip()}
        if errors := validate.problems(topic, names, texts):
            return JSONResponse({"errors": errors}, status_code=422)
        seed = secrets.randbelow(2 ** 31)
        m = mood.product(seed)
        store = app.state.store
        hid = store.create(names["a"], names["b"], texts["a"], texts["b"], seed,
                           {"hunger": m.hunger, "arousal": m.arousal}, topic)
        try:
            app.state.court.submit(hid)
        except court.Busy:
            store.delete(hid)
            return JSONResponse({"error": court.BUSY}, status_code=503)
        return {"id": hid}

    @app.get("/hearing/{hid}")
    def get_hearing(hid: str):
        h = app.state.store.get(hid)
        if h is None:
            return views.not_found()
        return views.hearing(h, app.state.store.appeal_of(hid) is not None)

    @app.get("/hearing/{hid}/brain")
    def get_brain(hid: str):
        h = app.state.store.get(hid)
        if h is None:
            return views.not_found()
        if h["status"] != "decided":
            return JSONResponse({"error": views.NOT_DECIDED}, status_code=409)
        return h["brain"]

    app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
    return app
