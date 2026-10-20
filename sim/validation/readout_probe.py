"""Sub-cascade readout probe (option 1, 2026-10-20). No model/smell changes.

Run from sim/:  PYTHONPATH=src uv run python -m validation.readout_probe
1. threshold: hearing pairs (both antennas) at falling input scales;
2. side + graded: one antenna at 1/4, 1/2, 1 x the threshold scale;
3. swap: all 25 steering-probe pairs at the threshold scale, both orders;
4. control: annotation sugar GRNs, one side, 200 Hz -> MN9 pair.
Per run: spike sums per (cell_class | side); ALPN split uni/multi.
"""
from functools import cache

import numpy as np
import pandas as pd

from borer_sim import anatomy, data, smell
from validation import steering
from validation.steering_probe import (PAIR_SEEDS, THREADS, WORKERS, X_TEXTS, Y_TEXTS,
                                       hearing, pair_jobs)
from validation.sugar_mn9 import OUT

SCALES = (0.02, 0.01, 0.005, 0.002, 0.001, 0.0005)
THRESHOLD_PAIRS = [("x_att", "y_att"), ("x_nat", "y_nat"), ("x_ave", "y_ave")]
SIDE_TEXTS = ("x_att", "x_nat", "x_ave")
LEVELS = (0.25, 0.5, 1.0)
SEEDS = PAIR_SEEDS[:5]
CASCADE_ACTIVE = 1000  # quiet runs had <= 107 active neurons, cascades >= 4,000
MN9_TYPE = "CB0701"


@cache
def _groups():
    a = data.annotations().reindex(data.neuron_ids())
    cls = a["cell_class"].where(a["cell_class"] != "ALPN",
                                "ALPN_" + a["cell_sub_class"].fillna("na").str[:5])
    key = cls.fillna(a["super_class"]).fillna("na") + "|" + a["side"].fillna("na")
    codes, uniq = pd.factorize(key.to_numpy())
    return codes, list(uniq), {s: anatomy.cell_type(MN9_TYPE, s) for s in anatomy.SIDES}


def pop_metrics(counts) -> dict:
    codes, uniq, mn9 = _groups()
    sums = np.bincount(codes, weights=counts, minlength=len(uniq))
    m = steering.metrics(counts)
    m["pop"] = {u: float(s) for u, s in zip(uniq, sums) if s}
    m["MN9"] = [float(counts[mn9[s]].sum()) for s in anatomy.SIDES]
    return m


def run(name, jobs):
    print(f"{name}: {len(jobs)} jobs", flush=True)
    return steering.run_jobs(jobs, OUT / name, WORKERS, THREADS, metric=pop_metrics)


def threshold_scale(res) -> float:
    """Largest scale with 0 cascades, provided every smaller scale is quiet too."""
    best = None
    for s in sorted(SCALES):
        if any(m["active"] > CASCADE_ACTIVE for k, m in res.items() if float(k.split("|")[0]) == s):
            break
        best = s
    return best


def unilateral(text, side, scale):
    return [(idx, r * scale) for idx, r in smell.drives(text, side)]


def main():
    thr = run("readout_threshold.jsonl", {
        f"{s}|{x}|{y}|{seed}": (hearing(X_TEXTS[x], Y_TEXTS[y], s), seed)
        for s in SCALES for x, y in THRESHOLD_PAIRS for seed in SEEDS})
    s_star = threshold_scale(thr)
    print(f"threshold scale: {s_star}", flush=True)
    if s_star is None:
        return
    run("readout_side.jsonl", {
        f"{lvl}|{t}|{side}|{seed}": (unilateral(X_TEXTS[t], side, s_star * lvl), seed)
        for lvl in LEVELS for t in SIDE_TEXTS for side in anatomy.SIDES for seed in SEEDS})
    run("readout_swap.jsonl", pair_jobs([(x, y) for x in X_TEXTS for y in Y_TEXTS], s_star))
    a = data.annotations()
    sugar = {s: data.to_index(a.index[(a["cell_sub_class"] == "sugar") & (a["side"] == s)]
                              .intersection(data.neuron_ids())) for s in anatomy.SIDES}
    run("readout_sugar.jsonl", {f"{side}|{seed}": ([(sugar[side], 200.0)], seed)
                                for side in anatomy.SIDES for seed in SEEDS})


if __name__ == "__main__":
    main()
