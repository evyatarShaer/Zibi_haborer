"""Tests marked `needs_data` are skipped when the v783 raw files are absent.
`sim` / `client`: the app on a temp DB with a fake simulation (fake.py).
`clock` / `store`: a case store on a temp DB with a settable clock (casekit.py).
`rig`: the page tests' server and headless Chrome (e2ekit.py, cdp.py).
The server secret (tokens.py) is a temp file, never api/data/secret.key."""
import os
import tempfile
import threading
import time

import pytest
import uvicorn
from fastapi.testclient import TestClient

os.environ["BORER_SECRET"] = os.path.join(tempfile.mkdtemp(), "secret.key")  # before borer_api

from borer_api.app import create_app
from borer_api.cases import Store
from borer_sim import data
from casekit import Clock
from cdp import Browser
from e2ekit import PORT, Script, Shift
from fake import FakeSim


def pytest_collection_modifyitems(items):
    if (data.RAW_DIR / "Connectivity_783.parquet").exists():
        return
    skip = pytest.mark.skip(reason="FlyWire v783 raw data not downloaded")
    for item in items:
        if "needs_data" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def sim():
    return FakeSim()


@pytest.fixture
def client(tmp_path, sim, clock):
    """The app with `sim` and the settable `clock`; the deadline sweep runs every 20 ms."""
    with TestClient(create_app(sim, str(tmp_path / "c.sqlite3"), sweep_every_s=0.02,
                               clock=clock)) as c:
        yield c


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def store(tmp_path, clock):
    s = Store(str(tmp_path / "c.sqlite3"), clock)
    yield s
    s.close()


@pytest.fixture(scope="module")
def rig(tmp_path_factory):
    """(sim, clock, browser) for the page tests: the app on PORT, headless Chrome."""
    sim, clock = Script(), Shift()
    app = create_app(sim, str(tmp_path_factory.mktemp("e2e") / "c.sqlite3"), sweep_every_s=0.2,
                     clock=clock)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)
    browser = Browser()
    yield sim, clock, browser
    browser.close()
    server.should_exit = True
    thread.join(10)  # the next test module binds the same port
    errors = [e["exception"]["description"] for e in browser.errors]
    assert not errors, errors[:3]  # no script error on any page
