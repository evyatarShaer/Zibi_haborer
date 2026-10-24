"""Readout metrics and SPEC §7 outcome rules (pure functions, no connectome)."""
import pytest

from borer_sim import readout
from borer_sim.params import OUTCOME

CLOSE, WIDE = OUTCOME["tie_gap"] / 2, OUTCOME["tie_gap"] * 2
LOW, HIGH = OUTCOME["froze_hz"] / 2, OUTCOME["froze_hz"] * 10


def m(a=HIGH, gap=WIDE, flips=0):
    b = a * (1 - gap) / (1 + gap)  # so that |a - b| / (a + b) == gap
    return {"A": a, "B": b, "gap": gap, "direction_flips": flips}


def test_flips_skip_zeros():
    assert readout.flips([1, 0, -2, 0, 0, 3, 1, -1]) == 3
    assert readout.flips([0, 0, 0]) == 0


def test_decision_time_when_cumulative_stays():
    d = OUTCOME["decision_spikes"]
    bin_ms = OUTCOME["readout_bin_ms"]
    assert readout.decision_time_ms([d, -d, 0, d, 0]) == 4 * bin_ms
    assert readout.decision_time_ms([-d, 0]) == bin_ms
    assert readout.decision_time_ms([1, -1]) is None
    assert readout.decision_time_ms([d - 1]) is None


def test_metrics_margin_gap_winner():
    out = readout.metrics([3, 1], [1, 1], 1.0)
    assert (out["A"], out["B"], out["winner"]) == (4.0, 2.0, "A")
    assert out["gap"] == pytest.approx(1 / 3) and out["margin"] == pytest.approx(2 / 3)
    assert readout.metrics([0], [0], 1.0)["winner"] is None


@pytest.mark.parametrize("case, hunger, expected", [
    (m(a=LOW, gap=CLOSE, flips=9), 1.0, "froze"),          # Froze beats food / dithered
    (m(a=LOW, gap=WIDE), 0.0, "froze"),                    # ... even with a wide gap
    (m(gap=CLOSE, flips=9), OUTCOME["food_hunger"] + 0.01, "food"),
    (m(gap=CLOSE), OUTCOME["food_hunger"], "tie"),         # hunger must be strictly above
    (m(gap=WIDE), 1.0, "win"),                             # hunger only matters when close
    (m(gap=CLOSE, flips=OUTCOME["dither_flips"]), 0.0, "dithered"),
    (m(gap=CLOSE, flips=OUTCOME["dither_flips"] - 1), 0.0, "tie"),
    (m(gap=WIDE, flips=99), 0.0, "win"),
    (m(gap=OUTCOME["tie_gap"]), 0.0, "win"),               # gap >= tie_gap is a win
])
def test_outcome_rules(case, hunger, expected):
    assert readout.outcome(case, hunger) == expected


def test_outcome_names_cover_rules():
    assert set(readout.OUTCOMES) == {"froze", "food", "dithered", "win", "tie"}
