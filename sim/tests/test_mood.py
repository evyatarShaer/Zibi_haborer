"""Mood: seeded per case, hunger rises while waiting, identical for both tastings."""
import numpy as np
import pytest
import torch

from borer_sim import mood, params, taste
from borer_sim.model import Model


def test_seeded_and_in_range():
    a, b = mood.from_case(42), mood.from_case(42)
    assert a == b and a != mood.from_case(43)
    for s in range(200):
        x = mood.from_case(s)
        assert 0 <= x.hunger <= params.MOOD["hunger_base_max"] and 0 <= x.arousal < params.MOOD["arousal_max"]


def test_hunger_rises_while_waiting_capped():
    base = mood.from_case(7)
    later = mood.from_case(7, wait_hours=3)
    assert later.hunger == pytest.approx(min(1.0, base.hunger + 3 * params.MOOD["hunger_per_hour"]))
    assert later.arousal == base.arousal
    assert mood.from_case(7, wait_hours=100) == later  # no wait counts past the deadline


def test_lunch_break_only_for_slow_answers():
    """0.25 / h (P2B-1): hunger passes 0.8 only after 1.6 h, and always at the deadline when
    the start is above 0.05."""
    bar = params.OUTCOME["food_hunger"]
    assert all(mood.from_case(s, 1.6).hunger <= bar for s in range(500))
    late = [mood.from_case(s, 3.0) for s in range(500)]
    assert all(m.hunger > bar for s, m in enumerate(late) if mood.from_case(s).hunger > 0.05)


def test_product_mood_simulated_wait():
    """No waiting time: the wait is drawn from the seed, so hunger can pass the food bar."""
    assert mood.product(42) == mood.product(42) != mood.product(43)
    ms = [mood.product(s) for s in range(2000)]
    assert all(0 <= m.hunger <= 1 and 0 <= m.arousal < params.MOOD["arousal_max"] for m in ms)
    assert all(m.arousal == mood.from_case(s).arousal for s, m in enumerate(ms))
    assert any(m.hunger > params.OUTCOME["food_hunger"] for m in ms)
    assert all(m.hunger >= mood.from_case(s).hunger for s, m in enumerate(ms))


def test_hunger_gains_only_exciting_groups():
    assert mood.Mood(0.0, 0.5).gains == {k: 1.0 for k in mood.EXCITING}
    g = mood.Mood(1.0, 0.0).gains
    assert set(g) == set(mood.EXCITING) and all(v == 1 + params.MOOD["hunger_gain"] for v in g.values())
    assert all(taste.TABLE[k][1].startswith("E") for k in g) and "מ" not in g


def _toy(n=50):
    """Unconnected neurons: every spike comes from input or a noise kick."""
    return Model(n, np.array([0]), np.array([1]), np.array([0]))


def test_noise_identical_for_both_tastings(monkeypatch):
    """Same seed: the noise realization does not depend on the argument's rates."""
    monkeypatch.setitem(params.MOOD, "noise_mv", 10.0)  # one + kick crosses threshold
    torch.set_num_threads(1)
    model, quiet = _toy(), list(range(10, 50))
    a = model.run([([0, 1], 50.0)], 500, seed=3, noise_hz=40.0)
    b = model.run([([0, 1], 300.0)], 500, seed=3, noise_hz=40.0)
    assert a.counts[quiet].sum() > 0
    np.testing.assert_array_equal(a.counts[quiet], b.counts[quiet])
    assert not np.array_equal(a.counts[:2], b.counts[:2])


def test_zero_noise_is_no_noise():
    model = _toy()
    a = model.run([([0, 1], 80.0)], 300, seed=5)
    b = model.run([([0, 1], 80.0)], 300, seed=5, noise_hz=0.0)
    np.testing.assert_array_equal(a.counts, b.counts)
