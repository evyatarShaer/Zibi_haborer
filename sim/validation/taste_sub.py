"""Taste subcircuit (P1-10): choose N, validate against the full brain, time hearings.

Run from sim/:  PYTHONPATH=src uv run python -m validation.taste_sub [sizes|ref|run N|check N|time N...]
Sources = every GRN in taste.mapping(); targets = MN9 + Giant Fiber, both sides.
Validation: NEW set arguments 0-9 x seeds 783-787 at 2 s, against the full-brain
results in taste_v3_new.jsonl (same seeds -> same Poisson input). Pass: per-argument
mean MN9 within +-5% (or +-0.5 Hz below 10 Hz) and the same winner on every pair.
Timing: a hearing = its two tastings in parallel, 2 processes x 1 thread.
"""
import multiprocessing as mp
import statistics
import sys
import time
from itertools import combinations

import numpy as np
import torch

from borer_sim import anatomy, data, subcircuit
from borer_sim.model import Model
from validation import taste
from validation.readout_probe import MN9_TYPE, pop_metrics
from validation.steering import _connectome_model, run_jobs
from validation.steering_probe import THREADS, WORKERS
from validation.steering_report import load
from validation.sugar_mn9 import OUT
from validation.taste_probe import DURATION_MS, RESULTS, tasting
from validation.taste_sets import PAIRS, SETS

ARGS, SEEDS = range(10), tuple(range(783, 788))
REL_TOL, ABS_TOL = 0.05, 0.5
_model = None


def _keep(n_hops: int) -> np.ndarray:
    sources = [i for _, ids in taste.mapping().values() for i in data.to_index(ids)]
    targets = [i for s in anatomy.SIDES
               for i in anatomy.cell_type(MN9_TYPE, s) + anatomy.giant_fiber(s)]
    return subcircuit.keep(sources, targets, n_hops)


def sizes():
    for n in range(2, 9):
        print(f"N = {n}: {len(_keep(n)):,} neurons", flush=True)


def _jobs() -> dict:
    return {f"{i}|{s}": (tasting(SETS["new"][i]), s) for i in ARGS for s in SEEDS}


def ref():
    """Full-brain reference: these keys are part of the NEW-set probe results."""
    run_jobs(_jobs(), OUT / RESULTS.format("new"), WORKERS, THREADS, metric=pop_metrics,
             duration_ms=DURATION_MS)


def run(n_hops):
    n_hops = int(n_hops)
    run_jobs(_jobs(), OUT / f"taste_sub_N{n_hops}.jsonl", WORKERS, THREADS, metric=pop_metrics,
             model=Model.subcircuit(_keep(n_hops)), duration_ms=DURATION_MS)


def check(n_hops):
    sub, full = load(f"taste_sub_N{n_hops}.jsonl"), load(RESULTS.format("new"))
    mn9 = {k: sum(m["MN9"]) for k, m in sub.items()}
    ref = {k: sum(full[k]["MN9"]) for k in sub}
    ok_rate = True
    for i in ARGS:
        a, b = (np.mean([d[f"{i}|{s}"] for s in SEEDS]) for d in (mn9, ref))
        good = abs(a - b) <= max(REL_TOL * b, ABS_TOL)
        ok_rate &= good
        print(f"  arg {i}: sub {a:6.1f}  full {b:6.1f}  {'ok' if good else 'OFF'}")
    same = total = 0
    for x, y in combinations(ARGS, 2):
        for s in SEEDS:
            w = [np.sign(d[f"{x}|{s}"] - d[f"{y}|{s}"]) for d in (mn9, ref)]
            same, total = same + (w[0] == w[1]), total + 1
    print(f"N = {n_hops}: MN9 within tolerance: {ok_rate}; same winner {same}/{total} "
          f"hearings (all 45 pairs x 5 seeds); bit-identical tastings "
          f"{sum(sub[k]['MN9'] == full[k]['MN9'] for k in sub)}/{len(sub)}")


def _taste(job):
    drives, seed = job
    torch.set_num_threads(1)
    _model.run(drives, DURATION_MS, seed)


def _hearing_times(model, n=10) -> list[float]:
    global _model
    _model = model
    hearings = [(tasting(SETS["new"][a]), tasting(SETS["new"][b])) for a, b in PAIRS["new"][:n]]
    times = []
    with mp.get_context("fork").Pool(2) as pool:
        for k, (x, y) in enumerate(hearings):
            t = time.perf_counter()
            pool.map(_taste, [(x, 783 + k), (y, 783 + k)], chunksize=1)
            times.append(time.perf_counter() - t)
    return times


def timing(*n_hops):
    full = _hearing_times(_connectome_model())
    mf = statistics.median(full)
    print(f"hearing (2 x {DURATION_MS / 1000:g} s tastings in parallel, 2 proc x 1 thread), "
          f"median of 10: full brain {mf:.2f} s {[round(t, 1) for t in full]}", flush=True)
    for n in map(int, n_hops):
        sub = _hearing_times(Model.subcircuit(_keep(n)))
        ms = statistics.median(sub)
        print(f"  subcircuit N={n}: {ms:.2f} s {[round(t, 1) for t in sub]}; "
              f"speed-up x{mf / ms:.1f}", flush=True)


if __name__ == "__main__":
    {"sizes": sizes, "ref": ref, "run": run, "check": check, "time": timing}[sys.argv[1]](*sys.argv[2:])
