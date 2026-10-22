"""Score the taste probe (validation.taste_probe) against the pre-set criteria.

Run from sim/:  PYTHONPATH=src uv run python -m validation.taste_report [screen|args|band [old|new|third] [ms] [file]|bench]
Per hearing (pair x seed), A/B = total MN9 rate of each tasting:
froze if both < FROZE_HZ; tie if gap = |A-B|/(A+B) < TIE_GAP; else win.
Pass rules (fixed before running): (a) >= 90% of non-trivial pairs (mean
gap >= 10%) have the majority winner in >= 75% of seeds; (b) tasting MN9
rates span a continuous range: <= 50% of tastings within any band 10% of the
range wide (replaced the gap-bin rule 2026-10-21, DECISIONS.md); (c) |Spearman rho| < 0.5 between
per-argument MN9 and length, and the count of ד/ב/ש; (d) Win >= 50% of
hearings; (e) runaway (> 4,000 active) in < 2% of tastings.
"""
import statistics
import sys
import time
from collections import defaultdict
from itertools import combinations

import numpy as np
import torch

from borer_sim import taste
from borer_sim.params import TASTING_MS
from validation.runner import RUNAWAY, connectome_model, load
from validation.taste_probe import RESULTS
from validation.taste_sets import PAIRS as SET_PAIRS, SETS

FROZE_HZ, TIE_GAP, NONTRIVIAL = 2.0, 0.05, 0.10
BAND, MAX_IN_BAND = 0.10, 0.50


def spearman(x, y):
    rx, ry = (np.argsort(np.argsort(v)) for v in (x, y))
    return float(np.corrcoef(rx, ry)[0, 1])


def densest_band(rates) -> tuple[float, float]:
    """Largest share of rates within any window BAND x (max - min) wide, and its start."""
    r = np.sort(np.asarray(rates, dtype=float))
    width = BAND * (r[-1] - r[0])
    counts = np.searchsorted(r, r + width, side="right") - np.arange(len(r))
    i = int(np.argmax(counts))
    return counts[i] / len(r), float(r[i])


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
    res = load(name or RESULTS.format(arg_set, int(ms)))
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
        honey = sum(taste.normalize(a).count(c) for c in "דבש")
        print(f"| {i} | {len(a)} | {honey} | {mean[i]:.1f} ± {np.std([x[0] for x in v]):.1f} | "
              f"{np.mean([x[1][0] for x in v]):.1f} / {np.mean([x[1][1] for x in v]):.1f} | {a} |")
    pairs(tot, seeds, mean, ARGUMENTS, SET_PAIRS[arg_set])
    m = [mean[i] for i in range(len(ARGUMENTS))]
    lens = [len(a) for a in ARGUMENTS]
    honey = [sum(taste.normalize(a).count(c) for c in "דבש") for a in ARGUMENTS]
    exc = [np.mean([taste.TABLE[c][1][0] == "E" for c in taste.normalize(a)
                    if c in taste.LETTERS]) for a in ARGUMENTS]
    print(f"\n(c) Spearman rho of per-argument MN9 with: length {spearman(m, lens):+.2f}, "
          f"ד/ב/ש count {spearman(m, honey):+.2f}, exciting-letter share (TABLE class E) "
          f"{spearman(m, exc):+.2f}")


def _outcome(x, y) -> str:
    """Hearing outcome from the two tastings' MN9: froze, tie, or the winner "a" / "b"."""
    if x < FROZE_HZ and y < FROZE_HZ:
        return "froze"
    if abs(x - y) / (x + y) < TIE_GAP:
        return "tie"
    return "a" if x > y else "b"


def longer_wins(tot, seeds, ARGUMENTS, pair_list) -> tuple[int, int]:
    """(decided hearings won by the longer text, decided hearings), equal lengths skipped."""
    won = decided = 0
    for a, b in pair_list:
        if len(ARGUMENTS[a]) == len(ARGUMENTS[b]):
            continue
        for s in seeds:
            o = _outcome(tot[a][s][0], tot[b][s][0])
            if o in "ab":
                w, other = (a, b) if o == "a" else (b, a)
                won, decided = won + (len(ARGUMENTS[w]) > len(ARGUMENTS[other])), decided + 1
    return won, decided


def pairs(tot, seeds, mean, ARGUMENTS, PAIRS):
    outcomes, consistent, gaps = defaultdict(int), [], []
    for a, b in PAIRS:
        wins = defaultdict(int)
        for s in seeds:
            o = _outcome(tot[a][s][0], tot[b][s][0])
            outcomes["win" if o in "ab" else o] += 1
            if o in "ab":
                wins[a if o == "a" else b] += 1
        gap = abs(mean[a] - mean[b]) / (mean[a] + mean[b]) if mean[a] + mean[b] else 0.0
        gaps.append(gap)
        if gap >= NONTRIVIAL:
            consistent.append(max(wins.values(), default=0) / len(seeds))
    n = sum(outcomes.values())
    ok = sum(c >= 0.75 for c in consistent)
    print(f"\n(a) non-trivial pairs (mean gap >= {NONTRIVIAL:.0%}): {len(consistent)}/{len(PAIRS)}; "
          f"consistency >= 75%: {ok}/{len(consistent)}; consistency values "
          f"{sorted(round(c, 1) for c in consistent)}")
    share, start = densest_band([v[0] for d in tot.values() for v in d.values()])
    print(f"(b) densest {BAND:.0%}-of-range band holds {share:.0%} of tastings (from {start:.1f} Hz; "
          f"pass <= {MAX_IN_BAND:.0%}); pair mean-gap quartiles "
          f"{np.round(np.percentile(gaps, [25, 50, 75]), 2).tolist()}")
    for label, pl in (("probe pairs", PAIRS), ("all pairs", list(combinations(range(len(ARGUMENTS)), 2)))):
        won, dec = longer_wins(tot, seeds, ARGUMENTS, pl)
        print(f"(c) longer text wins {won}/{dec} = {won / dec:.0%} of decided hearings ({label}; target 40-60%)")
    print(f"(d) outcomes over {n} hearings: " +
          ", ".join(f"{k} {v} ({v / n:.0%})" for k, v in sorted(outcomes.items())))


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
