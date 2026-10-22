"""Same seed → bit-identical spikes; a different seed → different spikes."""
import numpy as np
import pytest

from borer_sim import mood, readout, taste
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


def test_hearing_with_mood_bit_identical():
    """Same case seed + arguments + mood (hunger gain and arousal noise) → identical metrics."""
    model = Model.from_connectome()
    case = mood.from_case(783, wait_hours=2)
    assert case.hunger > 0 and case.noise_hz > 0
    args = ("פיצה עם אננס זה פשוט טעים ונקודה.", "הסדרה הזאת משעממת, בוא נראה משהו אחר.")
    runs = [readout.run_hearing(model, *args, case, 783, DURATION_MS) for _ in range(2)]
    assert runs[0] == runs[1]
    assert runs[0]["outcome"] in readout.OUTCOMES
