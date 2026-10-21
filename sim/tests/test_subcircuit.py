"""Subcircuit: path selection, and a subcircuit of every neuron equals the whole brain."""
import numpy as np
import pytest

from borer_sim import anatomy, subcircuit
from borer_sim.model import Model

pytestmark = pytest.mark.needs_data


def test_hops_on_a_chain():
    src, dst = np.array([0, 1, 2]), np.array([1, 2, 3])  # 0 -> 1 -> 2 -> 3, 4 isolated
    np.testing.assert_array_equal(subcircuit._hops(5, src, dst, [0], 2), [0, 1, 2, 3, 3])


def test_keep_contains_sources_and_targets():
    src, tgt = anatomy.orns("V", "left"), anatomy.giant_fiber("left")
    kept = subcircuit.keep(src, tgt, 2)
    assert set(src) | set(tgt) <= set(kept)


def test_full_subcircuit_is_bit_identical():
    full = Model.from_connectome()
    sub = Model.subcircuit(np.arange(full.n))
    drives = [(anatomy.orns("V", "left"), 100)]
    a, b = full.run(drives, 100, 7), sub.run(drives, 100, 7)
    np.testing.assert_array_equal(a.counts, b.counts)
    np.testing.assert_array_equal(a.active, b.active)
    np.testing.assert_array_equal(a.binned, b.binned)
