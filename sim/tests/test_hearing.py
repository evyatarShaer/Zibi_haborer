"""Product hearing (borer_sim.hearing): bit-identical per seed, group-level brain summary."""
import json

import pytest

from borer_sim import hearing, mood, readout, taste
from borer_sim.model import Model

pytestmark = pytest.mark.needs_data

MS = 300
ARGS = ("פיצה עם אננס זה פשוט טעים ונקודה.", "הסדרה הזאת משעממת, בוא נראה משהו אחר.")


@pytest.fixture(scope="module")
def runs():
    with hearing.workers(Model.from_connectome()) as pool:
        return [hearing.run(pool, *ARGS, seed, MS) for seed in (783, 783, 784)]


def test_forkserver_workers_match_fork(runs):
    """The API's start method (own model per worker) gives the same hearing as fork."""
    with hearing.workers(method="forkserver") as pool:
        r = hearing.run(pool, *ARGS, 783, MS)
    assert _strip(r) == _strip(runs[0])


def _strip(r):
    return {k: v for k, v in r.items() if k != "duration_ms"}


def test_same_seed_bit_identical(runs):
    a, b, _ = runs
    assert mood.product(783).noise_hz > 0  # mood and noise are part of what must repeat
    assert _strip(a) == _strip(b)
    assert a["metrics"]["outcome"] in readout.OUTCOMES


def test_different_seed_differs(runs):
    assert _strip(runs[0]) != _strip(runs[2])


def test_brain_summary_consistent_with_metrics(runs):
    r = runs[0]
    b, bin_s = r["brain"], r["brain"]["bin_ms"] / 1000
    assert b["seed"] == r["seed"] and b["mood"] == r["mood"] and b["sim_version"] == r["sim_version"]
    for side, rates in zip("AB", b["mn9_hz"]):
        assert len(rates) == MS // b["bin_ms"]
        assert sum(rates) * bin_s / (MS / 1000) == pytest.approx(r["metrics"][side])
    assert all(set(t) == set(taste.classes()) for t in b["taste_hz"])


def test_no_letter_level_data(runs):
    """SPEC §2.3: nothing per letter — no Hebrew letters, no GRN group (cell type) names."""
    text = json.dumps(runs[0], ensure_ascii=False)
    assert not any(c in text for c in taste.LETTERS + "ךםןףץ")
    groups = {name.split(":")[1].split("/")[0] for name, _ in taste.TABLE.values()}
    assert not any(g in text for g in groups)
