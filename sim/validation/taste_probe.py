"""Taste each argument alone; the one the fly wants to eat more wins (probe).

Run from sim/:
    PYTHONPATH=src uv run python -m validation.taste_probe screen
    PYTHONPATH=src uv run python -m validation.taste_probe tastings [old|new]
Validation only: no change to SPEC, model.py or smell.py. Argument sets: taste_sets.
"""
import sys

from borer_sim import data
from validation import steering, taste
from validation.readout_probe import pop_metrics
from validation.steering_probe import THREADS, WORKERS
from validation.sugar_mn9 import OUT
from validation.taste_sets import SETS

SEEDS = tuple(range(783, 793))
SCREEN_RATE, SCREEN_SEEDS = 150.0, (783, 784, 785)
DURATION_MS = 2000
RESULTS = "taste_v3_{}.jsonl"  # per set; earlier runs: taste_args.jsonl (1 s), taste_args_2s*.jsonl


def tasting(text: str):
    """One tasting: the argument on both sides of the labellum at once."""
    return taste.drives(text, "left") + taste.drives(text, "right")


def run(name, jobs, duration_ms=1000):
    print(f"{name}: {len(jobs)} jobs", flush=True)
    return steering.run_jobs(jobs, OUT / name, WORKERS, THREADS, metric=pop_metrics,
                             duration_ms=duration_ms)


def screen():
    """Every eligible GRN group alone, both sides, at SCREEN_RATE Hz per GRN."""
    groups = taste._groups(taste.grns())
    run("taste_screen.jsonl", {
        f"{name}|{seed}": ([(data.to_index(ids), SCREEN_RATE)], seed)
        for name, _, ids in groups for seed in SCREEN_SEEDS})


def tastings(arg_set="old"):
    for key, (name, ids) in taste.mapping().items():
        print(f"  {key} -> {name} ({len(ids)} GRNs)")
    run(RESULTS.format(arg_set), {f"{i}|{seed}": (tasting(a), seed)
                                  for i, a in enumerate(SETS[arg_set]) for seed in SEEDS},
        DURATION_MS)


if __name__ == "__main__":
    {"screen": screen, "tastings": tastings}[sys.argv[1]](*sys.argv[2:])
