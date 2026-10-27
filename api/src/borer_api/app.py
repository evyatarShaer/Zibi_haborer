"""HaBorer API (Phase 2B, SPEC §15): FastAPI around borer_sim + SQLite, serving web/.

Run: scripts/run_local.sh. Env: BORER_DB (default api/data/cases.sqlite3).
create_app(runner=...) takes a fake simulation for tests. Without one, the lifespan starts
the two tasting workers with "forkserver" (each builds its own model, so this threaded
process is never forked) and warms them up. It also starts the court, the deadline sweep
and the 7-day purge loop.
"""
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from borer_api import court, routes
from borer_api.cases import Store
from borer_api.db import cleanup_loop

ROOT = Path(__file__).resolve().parents[3]
DB = os.environ.get("BORER_DB", str(ROOT / "api" / "data" / "cases.sqlite3"))
WARMUP = "בדיקה קצרה של הזבוב לפני הדיון"


def real_runner():
    """(runner, pool): the product hearing on forkserver workers, warmed up."""
    from borer_sim import hearing
    pool = hearing.workers(method="forkserver")
    hearing.run(pool, WARMUP, WARMUP, 0, ms=100)
    return (lambda a, b, seed, wait_h: hearing.run(pool, a, b, seed, wait_h=wait_h)), pool


def create_app(runner=None, db_path: str = DB, purge_every_s: float = 3600,
               sweep_every_s: float = 30, clock=time.time) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        store, pool = Store(db_path, clock, max_active=court.MAX_ACTIVE), None
        store.requeue()
        run = runner
        if run is None:
            run, pool = real_runner()
        app.state.store, app.state.court = store, court.Court(store, run)
        stop = threading.Event()
        for name, loop, every in (("purge", lambda s, e: cleanup_loop(store, s, e), purge_every_s),
                                  ("deadline", app.state.court.sweep_loop, sweep_every_s)):
            threading.Thread(target=loop, args=(stop, every), name=name, daemon=True).start()
        yield
        stop.set()
        app.state.court.close()
        if pool is not None:
            pool.terminate()

    app = FastAPI(title="HaBorer", lifespan=lifespan)
    app.include_router(routes.router)

    def page(key: str = ""):
        """The page for /a/{token}, /b/{token}, /c/{case id} and /how (its script routes by
        path). Serving it binds nothing (SPEC §15.1)."""
        return FileResponse(ROOT / "web" / "index.html")

    for kind in "abc":
        app.add_api_route(f"/{kind}/{{key}}", page, include_in_schema=False)
    app.add_api_route("/how", page, include_in_schema=False)

    app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
    return app
