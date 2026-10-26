"""Tests marked `needs_data` are skipped when the v783 raw files are absent.
`sim` / `client`: the app on a temp DB with a fake simulation (fake.py).
`clock` / `store`: a case store on a temp DB with a settable clock (casekit.py)."""
import pytest
from fastapi.testclient import TestClient

from borer_api.app import create_app
from borer_api.cases import Store
from borer_sim import data
from casekit import Clock
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
