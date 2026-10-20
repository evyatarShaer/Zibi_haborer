"""borer_sim.model reproduces the Brian2 port spike for spike on a small net.

Driving at 10 kHz makes every Poisson draw a hit (p = rate * dt = 1), so
both engines see identical input and must agree exactly. The net covers
integration, delay, inhibition, threshold, reset and refractoriness.
"""
import numpy as np
from brian2 import ms

from borer_sim.model import Model
from borer_sim.params import BIN_MS
from validation import shiu_brian2

EDGES = (3, np.array([0, 1, 2]), np.array([1, 2, 1]), np.array([2, 110, -18]))
DRIVES = [([0], 10_000)]
DURATION_MS = 500


def brian2_binned():
    net, mon = shiu_brian2.build(DRIVES, edges=EDGES)
    net.run(DURATION_MS * ms)
    step_bins = np.floor(np.asarray(mon.t / ms) / BIN_MS + 1e-9).astype(int)
    out = np.zeros((round(DURATION_MS / BIN_MS), EDGES[0]), dtype=np.int32)
    np.add.at(out, (step_bins, np.asarray(mon.i)), 1)
    return out


def test_matches_brian2_exactly():
    r = Model(*EDGES).run(DRIVES, DURATION_MS, seed=0)
    full = np.zeros((r.binned.shape[0], EDGES[0]), dtype=np.int32)
    full[:, r.active] = r.binned
    ref = brian2_binned()
    assert ref[:, 1].sum() > 10 and ref[:, 2].sum() > 3  # the net is really active
    np.testing.assert_array_equal(full, ref)
