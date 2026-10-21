"""Score the taste probe (validation.taste_probe) against the pre-set criteria.

Run from sim/:  PYTHONPATH=src uv run python -m validation.taste_report [screen|args|band [file]|bench]
Per hearing (pair x seed), A/B = total MN9 rate of each tasting:
froze if both < FROZE_HZ; tie if gap = |A-B|/(A+B) < TIE_GAP; else win.
Pass rules (fixed before running): (a) >= 90% of non-trivial pairs (mean
gap >= 10%) have the majority winner in >= 75% of seeds; (b) mean pair
gaps fill >= 3 of 4 bins with >= 10% each; (c) |Spearman rho| < 0.5 between
per-argument MN9 and length, and the count of ד/ב/ש; (d) Win >= 50% of
hearings; (e) runaway (> 4,000 active) in < 2% of tastings.
"""
import statistics
import sys
import time
from collections import defaultdict

import numpy as np
import torch

from borer_sim import smell
from validation.proto_report import RUNAWAY
from validation.steering_report import load
from validation.taste_probe import ARGS_FILE, ARGUMENTS, DURATION_MS, PAIRS, tasting

FROZE_HZ, TIE_GAP, NONTRIVIAL = 2.0, 0.05, 0.10
BINS = (0.0, 0.1, 0.3, 0.6, 1.0001)


def spearman(x, y):
    rx, ry = (np.argsort(np.argsort(v)) for v in (x, y))
    return float(np.corrcoef(rx, ry)[0, 1])


def screen():
    by = defaultdict(list)
    for key, m in load("taste_screen.jsonl").items():
        by[key.split("|")[0]].append(m)
    print("| GRN group | active (3 seeds) | runaway | MN9 L+R |\n|---|---|---|---|")
    for g, ms in sorted(by.items(), key=lambda kv: -max(m["active"] for m in kv[1])):
        act = [m["active"] for m in ms]
        print(f"| {g} | {' / '.join(map(str, act))} | {sum(a > RUNAWAY for a in act)}/3 | "
              f"{statistics.mean(sum(m['MN9']) for m in ms):.1f} |")


def args(name=ARGS_FILE):
    res = load(name)
    tot = defaultdict(dict)
    for key, m in res.items():
        i, seed = key.split("|")
        tot[int(i)][seed] = (sum(m["MN9"]), m["MN9"], m["active"])
    seeds = sorted(next(iter(tot.values())))
    act = [v[2] for d in tot.values() for v in d.values()]
    print(f"Tastings {len(act)}; runaway: {sum(a > RUNAWAY for a in act)}/{len(act)} "
          f"({np.mean([a > RUNAWAY for a in act]):.1%}); active median {np.median(act):.0f}\n")
    mean = {i: np.mean([tot[i][s][0] for s in seeds]) for i in tot}
    print("| # | chars | ד/ב/ש | MN9 total Hz (mean ± sd) | MN9 L / R | text |\n|---|---|---|---|---|---|")
    for i, a in enumerate(ARGUMENTS):
        v = [tot[i][s] for s in seeds]
        honey = sum(smell.normalize(a).count(c) for c in "דבש")
        print(f"| {i} | {len(a)} | {honey} | {mean[i]:.1f} ± {np.std([x[0] for x in v]):.1f} | "
              f"{np.mean([x[1][0] for x in v]):.1f} / {np.mean([x[1][1] for x in v]):.1f} | {a} |")
    pairs(tot, seeds, mean)
    m = [mean[i] for i in range(len(ARGUMENTS))]
    lens = [len(a) for a in ARGUMENTS]
    honey = [sum(smell.normalize(a).count(c) for c in "דבש") for a in ARGUMENTS]
    att = [np.mean([smell.LETTERS[c][1] == smell.ATTRACTIVE for c in smell.normalize(a)
                    if c in smell.LETTERS]) for a in ARGUMENTS]
    print(f"\n(c) Spearman rho of per-argument MN9 with: length {spearman(m, lens):+.2f}, "
          f"ד/ב/ש count {spearman(m, honey):+.2f}, attractive-letter share {spearman(m, att):+.2f}")


def pairs(tot, seeds, mean):
    outcomes, consistent, gaps = defaultdict(int), [], []
    longer_wins = decided = 0
    for a, b in PAIRS:
        wins = defaultdict(int)
        for s in seeds:
            x, y = tot[a][s][0], tot[b][s][0]
            if x < FROZE_HZ and y < FROZE_HZ:
                outcomes["froze"] += 1
            elif abs(x - y) / (x + y) < TIE_GAP:
                outcomes["tie"] += 1
            else:
                outcomes["win"] += 1
                w = a if x > y else b
                wins[w] += 1
                decided += 1
                longer_wins += len(ARGUMENTS[w]) > len(ARGUMENTS[b if w == a else a])
        gap = abs(mean[a] - mean[b]) / (mean[a] + mean[b]) if mean[a] + mean[b] else 0.0
        gaps.append(gap)
        if gap >= NONTRIVIAL:
            consistent.append(max(wins.values(), default=0) / len(seeds))
    n = sum(outcomes.values())
    ok = sum(c >= 0.75 for c in consistent)
    print(f"\n(a) non-trivial pairs (mean gap >= {NONTRIVIAL:.0%}): {len(consistent)}/{len(PAIRS)}; "
          f"consistency >= 75%: {ok}/{len(consistent)}; consistency values "
          f"{sorted(round(c, 1) for c in consistent)}")
    hist = np.histogram(gaps, bins=BINS)[0]
    print(f"(b) pair mean-gap bins {list(zip(BINS[:-1], hist.tolist()))}; quartiles "
          f"{np.round(np.percentile(gaps, [25, 50, 75]), 2).tolist()}")
    print(f"(c) longer text wins {longer_wins}/{decided} decided hearings")
    print(f"(d) outcomes over {n} hearings: " +
          ", ".join(f"{k} {v} ({v / n:.0%})" for k, v in sorted(outcomes.items())))


def band(name=ARGS_FILE):
    """Tie-band sweep: a hearing is decided if not froze and gap >= band. Consistent =
    decided hearings that agree with their pair's majority decided winner."""
    tot = defaultdict(dict)
    for key, m in load(name).items():
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
    from validation.steering import _connectome_model
    torch.set_num_threads(2)
    model = _connectome_model()
    a, b = PAIRS[0]
    times = []
    for k in range(5):
        t = time.perf_counter()
        model.run(tasting(ARGUMENTS[a]), DURATION_MS, 783 + k)
        model.run(tasting(ARGUMENTS[b]), DURATION_MS, 883 + k)
        times.append(time.perf_counter() - t)
    print(f"(f) full hearing (2 tastings x {DURATION_MS / 1000:g} s, 2 threads): median {statistics.median(times):.2f} s, "
          f"runs {[round(x, 2) for x in times]}")


if __name__ == "__main__":
    {"screen": screen, "args": args, "band": band, "bench": bench}[sys.argv[1] if len(sys.argv) > 1 else "args"](
        *sys.argv[2:])
