"""P1-9 exit criteria (SPEC §12) on the balance run's records (validation.balance).

Reads sim/data/processed/validation/balance_1500ms.jsonl; skipped until the run is complete
(`PYTHONPATH=src:. uv run python -m validation.balance run`, then `... time`).
"""
import json

import pytest

from validation import balance
from validation.sugar_mn9 import OUT

pytestmark = pytest.mark.needs_data


@pytest.fixture(scope="module")
def summary():
    try:
        return balance.summary()
    except (FileNotFoundError, KeyError):
        pytest.skip("balance run missing or incomplete")


def test_side_a_wins_45_55(summary):
    assert 0.45 <= summary["a_wins"] <= 0.55


def test_seed_consistency(summary):
    c = summary["consistent"]
    assert c and sum(x >= 0.75 for x in c) >= 0.9 * len(c)


def test_outcome_mix(summary):
    mix = summary["outcomes"]
    assert mix.get("win", 0) >= 0.5
    assert all(share <= 0.15 for o, share in mix.items() if o not in ("win", "tie"))  # SPEC §12


def test_runaway_below_2_percent(summary):
    assert summary["runaway"] < 0.02


def test_longer_wins_40_60(summary):
    assert 0.40 <= summary["longer_wins"] <= 0.60


def test_hearing_time_and_product_path():
    path = OUT / balance.TIME_FILE
    if not path.exists():
        pytest.skip("balance timing not run")
    row = json.loads(path.read_text())
    assert row["median_s"] <= 15
    assert row["records_match"] == f"{balance.TIME_N}/{balance.TIME_N}"
