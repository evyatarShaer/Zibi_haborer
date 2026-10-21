"""Length-effect diagnostic for the taste probe (validation only).

Run from sim/:  PYTHONPATH=src uv run python -m validation.taste_length [run|balanced|report]
E1 "repeat": short arguments without ! or ?, repeated x1..x4; letter shares
and distinct letters stay fixed, only the length gain grows.
E2 "flat": all 20 arguments with the length gain fixed at 1 (no verbose "!").
"balanced": the 20 arguments, 1 s x 5 seeds, scored with `taste_report args <file>`.
"average": synthetic "average Hebrew" texts (letters at CHAT_FREQ) of
growing length: where a long text's letter mix lands on MN9.
Input versions (rerunning measures the current taste.letter_rates): E1/E2 and
taste_len_average.jsonl used raw shares; taste_len_balanced.jsonl raw shares +
fixed total (commit 0792bb9); default files: frequency-relative + fixed total.
"""
import sys
from collections import defaultdict
from contextlib import contextmanager

import numpy as np

from borer_sim import smell
from validation.letter_freq import CHAT_FREQ
from validation.steering_report import load
from validation.taste_probe import run, tasting
from validation.taste_sets import OLD as ARGUMENTS
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


def balanced(name="taste_len_relative.jsonl"):
    run(name, {f"{i}|{s}": (tasting(a), s)
                                     for i, a in enumerate(ARGUMENTS) for s in SEEDS})


def average_text(n_chars: int) -> str:
    """Letters at conversational Hebrew frequency, a space after every 5th letter."""
    n = round(n_chars * 5 / 6)
    letters = "".join(l * round(f * n) for l, f in CHAT_FREQ.items())
    return " ".join(letters[i:i + 5] for i in range(0, len(letters), 5))


def average(name="taste_len_avg_relative.jsonl"):
    run(name, {f"avg{n}|{s}": (tasting(average_text(n)), s)
                                    for n in (40, 80, 140, 280) for s in SEEDS})


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
    {"run": experiments, "balanced": balanced, "average": average,
     "report": report}[sys.argv[1]](*sys.argv[2:])
