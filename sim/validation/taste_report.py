"""Score the taste probe (validation.taste_probe) against the pre-set criteria.

Run from sim/:  PYTHONPATH=src uv run python -m validation.taste_report [screen|args|band [old|new|third] [ms] [file]|bench]
Pass rules and their computation: validation.taste_criteria.
"""
import statistics
import sys
import time
from collections import defaultdict

import numpy as np
import torch

from borer_sim import taste
from borer_sim.params import TASTING_MS
from validation.runner import RUNAWAY, connectome_model, load
from validation.taste_probe import RESULTS
from validation.taste_criteria import FROZE_HZ, criteria, print_criteria, tastings
from validation.taste_sets import PAIRS as SET_PAIRS, SETS

def screen():
    by = defaultdict(list)
    for key, m in load("taste_screen.jsonl").items():
        by[key.split("|")[0]].append(m)
    print("| GRN group | active (3 seeds) | runaway | MN9 L+R |\n|---|---|---|---|")
    for g, ms in sorted(by.items(), key=lambda kv: -max(m["active"] for m in kv[1])):
        act = [m["active"] for m in ms]
        print(f"| {g} | {' / '.join(map(str, act))} | {sum(a > RUNAWAY for a in act)}/3 | "
              f"{statistics.mean(sum(m['MN9']) for m in ms):.1f} |")


def args(arg_set="third", ms=TASTING_MS, name=None):
    ARGUMENTS = SETS[arg_set]
    tot = tastings(load(name or RESULTS.format(arg_set, int(ms))))
    c = criteria(tot, ARGUMENTS, SET_PAIRS[arg_set])
    print(f"Tastings {len(c['active'])}\n")
    print("| # | chars | ד/ב/ש | MN9 total Hz (mean ± sd) | MN9 L / R | text |\n|---|---|---|---|---|---|")
    for i, a in enumerate(ARGUMENTS):
        v = [tot[i][s] for s in c["seeds"]]
        honey = sum(taste.normalize(a).count(ch) for ch in "דבש")
        print(f"| {i} | {len(a)} | {honey} | {c['mean'][i]:.1f} ± {np.std([x[0] for x in v]):.1f} | "
              f"{np.mean([x[1][0] for x in v]):.1f} / {np.mean([x[1][1] for x in v]):.1f} | {a} |")
    print_criteria(c)


def band(arg_set="third", ms=TASTING_MS, name=None):
    """Tie-band sweep: a hearing is decided if not froze and gap >= band. Consistent =
    decided hearings that agree with their pair's majority decided winner."""
    tot = defaultdict(dict)
    ARGUMENTS, PAIRS = SETS[arg_set], SET_PAIRS[arg_set]
    for key, m in load(name or RESULTS.format(arg_set, int(ms))).items():
        i, seed = key.split("|")
        tot[int(i)][seed] = sum(m["MN9"])
    seeds = sorted(next(iter(tot.values())))
    print("| tie band | Win share | decided consistent | pairs >= 75% | longer wins |\n|---|---|---|---|---|")
    for b in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50):
        win = agree = longer = 0
        good = npairs = 0
        for a, c in PAIRS:
            w = defaultdict(int)
            for s in seeds:
                x, y = tot[a][s], tot[c][s]
                if not (x < FROZE_HZ and y < FROZE_HZ) and abs(x - y) / (x + y) >= b:
                    w[a if x > y else c] += 1
            n = sum(w.values())
            if n:
                top = max(w, key=w.get)
                win, agree, npairs = win + n, agree + w[top], npairs + 1
                good += w[top] / n >= 0.75
                longer += w[a if len(ARGUMENTS[a]) > len(ARGUMENTS[c]) else c]
        print(f"| {b:.0%} | {win / (len(PAIRS) * len(seeds)):.0%} | {agree / win:.1%} | "
              f"{good}/{npairs} | {longer / win:.0%} |")


def bench():
    torch.set_num_threads(2)
    model = connectome_model()
    a, b = SET_PAIRS["old"][0]
    ARGUMENTS = SETS["old"]
    times = []
    for k in range(5):
        t = time.perf_counter()
        model.run(taste.tasting(ARGUMENTS[a]), TASTING_MS, 783 + k)
        model.run(taste.tasting(ARGUMENTS[b]), TASTING_MS, 883 + k)
        times.append(time.perf_counter() - t)
    print(f"(f) full hearing (2 tastings x {TASTING_MS / 1000:g} s, 2 threads): median {statistics.median(times):.2f} s, "
          f"runs {[round(x, 2) for x in times]}")


if __name__ == "__main__":
    {"screen": screen, "args": args, "band": band, "bench": bench}[sys.argv[1] if len(sys.argv) > 1 else "args"](
        *sys.argv[2:])
