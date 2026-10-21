"""Length-effect diagnostic for the taste probe (validation only).

Run from sim/:  PYTHONPATH=src uv run python -m validation.taste_length [run|balanced|report]
E1 "repeat": short arguments without ! or ?, repeated x1..x4; letter shares
and distinct letters stay fixed, only the length gain grows.
E2 "flat": all 20 arguments with the length gain fixed at 1 (no verbose "!").
E1/E2 data were made before taste.letter_rates fixed the total drive; rerunning
them now would measure the fixed input. "balanced": the fixed input, 1 s x 5
seeds, scored with `taste_report args taste_len_balanced.jsonl`.
"""
import sys
from collections import defaultdict
from contextlib import contextmanager

import numpy as np

from borer_sim import smell
from validation.steering_report import load
from validation.taste_probe import ARGUMENTS, run, tasting
from validation.taste_report import spearman

SHORT = (3, 5, 8, 11, 14, 16)
REPS = (1, 2, 3, 4)
SEEDS = tuple(range(783, 788))


@contextmanager
def flat_gain():
    real = smell.length_gain
    # 1 everywhere; max_chars keeps a different value so the "excess" term is 0, not 0/0
    smell.length_gain = lambda n: 1.0 if n != smell.SMELL["max_chars"] else 2.0
    try:
        yield
    finally:
        smell.length_gain = real


def experiments():
    run("taste_len_repeat.jsonl", {f"{i}x{r}|{s}": (tasting(" ".join([ARGUMENTS[i]] * r)), s)
                                   for i in SHORT for r in REPS for s in SEEDS})
    with flat_gain():
        jobs = {f"{i}|{s}": (tasting(a), s) for i, a in enumerate(ARGUMENTS) for s in SEEDS}
    run("taste_len_flat.jsonl", jobs)


def balanced():
    run("taste_len_balanced.jsonl", {f"{i}|{s}": (tasting(a), s)
                                     for i, a in enumerate(ARGUMENTS) for s in SEEDS})


def mn9(name) -> dict:
    by = defaultdict(list)
    for key, m in load(name).items():
        by[key.split("|")[0]].append(sum(m["MN9"]))
    return {k: float(np.mean(v)) for k, v in by.items()}


def report():
    rep = mn9("taste_len_repeat.jsonl")
    print("E1 MN9 Hz by repeat (gain " + " / ".join(
        f"x{r} {smell.length_gain(len(smell.normalize(' '.join([ARGUMENTS[3]] * r)))):.2f}"
        for r in REPS) + ")")
    for i in SHORT:
        print(f"  #{i}: " + " / ".join(f"{rep[f'{i}x{r}']:.1f}" for r in REPS))
    flat, base = mn9("taste_len_flat.jsonl"), mn9("taste_args.jsonl")
    lens = [len(a) for a in ARGUMENTS]
    for name, d in (("1 s baseline", base), ("E2 flat gain", flat)):
        m = [d[str(i)] for i in range(len(ARGUMENTS))]
        print(f"{name}: rho(MN9, length) {spearman(m, lens):+.2f}; MN9 " +
              " ".join(f"{v:.0f}" for v in m))


if __name__ == "__main__":
    {"run": experiments, "balanced": balanced, "report": report}[sys.argv[1]]()
