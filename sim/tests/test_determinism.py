"""Same seed → bit-identical spikes; a different seed → different spikes."""
import numpy as np
import pytest

from borer_sim import taste
from borer_sim.model import Model
from borer_sim.params import BIN_MS

pytestmark = pytest.mark.needs_data

DURATION_MS = 300


@pytest.fixture(scope="module")
def runs():
    model = Model.from_connectome()
    drives = taste.tasting("אתה תמיד שוכח לסגור את הדלת, וזה ממש מעצבן אותי!")
    return [model.run(drives, DURATION_MS, seed) for seed in (7, 7, 8)]


def test_same_seed_bit_identical(runs):
    a, b, _ = runs
    assert a.counts.sum() > 0
    np.testing.assert_array_equal(a.counts, b.counts)
    np.testing.assert_array_equal(a.active, b.active)
    np.testing.assert_array_equal(a.binned, b.binned)


def test_different_seed_differs(runs):
    a, _, c = runs
    assert not np.array_equal(a.counts, c.counts)


def test_binned_consistent_with_counts(runs):
    r = runs[0]
    assert r.binned.shape[0] == DURATION_MS // BIN_MS
    np.testing.assert_array_equal(r.binned.sum(0), r.counts[r.active])

