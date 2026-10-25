"""Tests marked `needs_data` are skipped when the v783 raw files are absent.
`sim` / `client`: the app on a temp DB with a fake simulation (fake.py)."""
import pytest
from fastapi.testclient import TestClient

from borer_api.app import create_app
from borer_sim import data
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
def client(tmp_path, sim):
    with TestClient(create_app(sim, str(tmp_path / "h.sqlite3"))) as c:
        yield c
