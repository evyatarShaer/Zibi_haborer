"""borer_sim.data loads the v783 tables with the schema DATA_SOURCES.md records."""
import pandas as pd
import pytest

from borer_sim import data

pytestmark = pytest.mark.skipif(
    not (data.RAW_DIR / "Connectivity_783.parquet").exists(),
    reason="FlyWire v783 raw data not downloaded",
)


def test_row_counts():
    assert len(data.neuron_ids()) == 138_639
    assert len(data.connectivity()) == 15_091_983
    assert len(data.annotations()) == 139_248


def test_connectivity_index_matches_completeness_order():
    ids = data.neuron_ids().to_numpy()
    raw = pd.read_parquet(data.RAW_DIR / "Connectivity_783.parquet",
                          columns=["Presynaptic_ID", "Presynaptic_Index",
                                   "Postsynaptic_ID", "Postsynaptic_Index"])
    assert (ids[raw["Presynaptic_Index"]] == raw["Presynaptic_ID"]).all()
    assert (ids[raw["Postsynaptic_Index"]] == raw["Postsynaptic_ID"]).all()


def test_to_index_roundtrip_and_unknown():
    ids = data.neuron_ids()
    assert data.to_index([ids[0], ids[-1]]) == [0, len(ids) - 1]
    with pytest.raises(KeyError):
        data.to_index([1])
