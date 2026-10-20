"""Tests marked `needs_data` are skipped when the v783 raw files are absent."""
import pytest

from borer_sim import data


def pytest_collection_modifyitems(items):
    if (data.RAW_DIR / "Connectivity_783.parquet").exists():
        return
    skip = pytest.mark.skip(reason="FlyWire v783 raw data not downloaded")
    for item in items:
        if "needs_data" in item.keywords:
            item.add_marker(skip)
