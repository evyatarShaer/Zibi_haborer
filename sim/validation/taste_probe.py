"""Taste each argument alone; the one the fly wants to eat more wins (probe).

Run from sim/:
    PYTHONPATH=src uv run python -m validation.taste_probe screen
    PYTHONPATH=src uv run python -m validation.taste_probe tastings [old|new|third] [ms] [N]
N = run on the taste subcircuit of N hops (validation.taste_sub); results are
bit-identical to the full brain for N = 6, so they go to the same file.
Input: borer_sim.taste. Argument sets: taste_sets.
"""
import sys

from borer_sim import data, taste
from borer_sim.params import TASTING_MS
from validation.runner import run_jobs
from validation.sugar_mn9 import OUT
from validation.taste_sets import SETS

SEEDS = tuple(range(783, 793))
SCREEN_RATE, SCREEN_SEEDS = 150.0, (783, 784, 785)
RESULTS = "taste_v4_{}_{}ms.jsonl"  # (set, ms); v3 table (0.3.0): taste_v3_{old,new}.jsonl (2 s)


def run(name, jobs, duration_ms=1000, model=None):
    print(f"{name}: {len(jobs)} jobs", flush=True)
    return run_jobs(jobs, OUT / name, duration_ms, model)


def screen():
    """Every eligible GRN group alone, both sides, at SCREEN_RATE Hz per GRN."""
    run("taste_screen.jsonl", {
        f"{name}|{seed}": ([(data.to_index(ids), SCREEN_RATE)], seed)
        for name, ids in taste.groups().items() for seed in SCREEN_SEEDS})


def tastings(arg_set="third", ms=TASTING_MS, n_hops=None):
    model = None
    if n_hops is not None:
        from borer_sim.model import Model
        from validation.taste_sub import _keep  # taste_sub imports this module
        model = Model.subcircuit(_keep(int(n_hops)))
    for key, (name, ids) in taste.mapping().items():
        print(f"  {key} -> {name} ({len(ids)} GRNs)")
    run(RESULTS.format(arg_set, int(ms)), {f"{i}|{seed}": (taste.tasting(a), seed)
                                           for i, a in enumerate(SETS[arg_set]) for seed in SEEDS},
        int(ms), model)


if __name__ == "__main__":
    {"screen": screen, "tastings": tastings}[sys.argv[1]](*sys.argv[2:])
