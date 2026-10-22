"""Taste-probe pass rules (fixed before running), computed as values.

Per hearing (pair x seed), A/B = total MN9 rate of each tasting:
froze if both < FROZE_HZ; tie if gap = |A-B|/(A+B) < TIE_GAP; else win.
(a) >= 90% of non-trivial pairs (mean gap >= 10%) have the majority winner in
>= 75% of seeds; (b) <= 50% of tastings within any band 10% of the MN9 range wide;
(c) |Spearman rho| < 0.5 between per-argument MN9 and length, and the count of
ד/ב/ש; (d) Win >= 50% of hearings; (e) runaway (> 4,000 active) in < 2% of
tastings; longer text wins 40-60% of decided hearings over ALL pairs of the set
(probe pairs printed for reference only; DECISIONS.md 2026-10-22, SIM_VERSION 0.6.0).
"""
from collections import defaultdict
from itertools import combinations

import numpy as np

from borer_sim import taste
from validation.runner import RUNAWAY

FROZE_HZ, TIE_GAP, NONTRIVIAL = 2.0, 0.05, 0.10
BAND, MAX_IN_BAND = 0.10, 0.50
LONGER = (0.40, 0.60)


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


def tastings(res: dict) -> dict:
    """{arg index: {seed: (MN9 total, MN9 [L, R], active)}} from probe records."""
    tot = defaultdict(dict)
    for key, m in res.items():
        i, seed = key.split("|")
        tot[int(i)][seed] = (sum(m["MN9"]), m["MN9"], m["active"])
    return tot


def outcome(x, y) -> str:
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
            o = outcome(tot[a][s][0], tot[b][s][0])
            if o in "ab":
                w, other = (a, b) if o == "a" else (b, a)
                won, decided = won + (len(ARGUMENTS[w]) > len(ARGUMENTS[other])), decided + 1
    return won, decided


def criteria(tot, ARGUMENTS, PAIRS) -> dict:
    """Every pass rule's value, plus "pass": {rule: bool}."""
    seeds = sorted(next(iter(tot.values())))
    mean = {i: float(np.mean([tot[i][s][0] for s in seeds])) for i in tot}
    outcomes, consistent, gaps = defaultdict(int), [], []
    for a, b in PAIRS:
        wins = defaultdict(int)
        for s in seeds:
            o = outcome(tot[a][s][0], tot[b][s][0])
            outcomes["win" if o in "ab" else o] += 1
            if o in "ab":
                wins[a if o == "a" else b] += 1
        gap = abs(mean[a] - mean[b]) / (mean[a] + mean[b]) if mean[a] + mean[b] else 0.0
        gaps.append(gap)
        if gap >= NONTRIVIAL:
            consistent.append(max(wins.values(), default=0) / len(seeds))
    act = [v[2] for d in tot.values() for v in d.values()]
    m = [mean[i] for i in range(len(ARGUMENTS))]
    honey = [sum(taste.normalize(a).count(c) for c in "דבש") for a in ARGUMENTS]
    exc = [np.mean([taste.TABLE[c][1][0] == "E" for c in taste.normalize(a) if c in taste.LETTERS])
           for a in ARGUMENTS]
    longer = {label: longer_wins(tot, seeds, ARGUMENTS, pl) for label, pl in
              (("probe pairs", PAIRS), ("all pairs", list(combinations(range(len(ARGUMENTS)), 2))))}
    c = {"mean": mean, "seeds": seeds, "consistent": consistent, "gaps": gaps,
         "band": densest_band([v[0] for d in tot.values() for v in d.values()]),
         "rho_len": spearman(m, [len(a) for a in ARGUMENTS]), "rho_honey": spearman(m, honey),
         "rho_exc": spearman(m, exc), "outcomes": dict(outcomes), "active": act,
         "runaway": float(np.mean([a > RUNAWAY for a in act])), "longer": longer}
    n = sum(outcomes.values())
    c["pass"] = {
        "a": sum(x >= 0.75 for x in consistent) >= 0.9 * len(consistent),
        "b": c["band"][0] <= MAX_IN_BAND,
        "c": abs(c["rho_len"]) < 0.5 and abs(c["rho_honey"]) < 0.5,
        "d": outcomes["win"] / n >= 0.5,
        "e": c["runaway"] < 0.02,
        "longer": LONGER[0] <= longer["all pairs"][0] / longer["all pairs"][1] <= LONGER[1]}
    return c


def print_criteria(c):
    ok = sum(x >= 0.75 for x in c["consistent"])
    print(f"\n(a) non-trivial pairs (mean gap >= {NONTRIVIAL:.0%}): {len(c['consistent'])}/{len(c['gaps'])}; "
          f"consistency >= 75%: {ok}/{len(c['consistent'])}; consistency values "
          f"{sorted(round(x, 1) for x in c['consistent'])}")
    share, start = c["band"]
    print(f"(b) densest {BAND:.0%}-of-range band holds {share:.0%} of tastings (from {start:.1f} Hz; "
          f"pass <= {MAX_IN_BAND:.0%}); pair mean-gap quartiles "
          f"{np.round(np.percentile(c['gaps'], [25, 50, 75]), 2).tolist()}")
    for label, (won, dec) in c["longer"].items():
        rule = "target 40-60%" if label == "all pairs" else "reference only"
        print(f"(c) longer text wins {won}/{dec} = {won / dec:.0%} of decided hearings ({label}; {rule})")
    n = sum(c["outcomes"].values())
    print(f"(d) outcomes over {n} hearings: " +
          ", ".join(f"{k} {v} ({v / n:.0%})" for k, v in sorted(c["outcomes"].items())))
    act = c["active"]
    print(f"(e) runaway {sum(a > RUNAWAY for a in act)}/{len(act)} ({c['runaway']:.1%}); "
          f"active median {np.median(act):.0f}")
    print(f"(c) Spearman rho of per-argument MN9 with: length {c['rho_len']:+.2f}, "
          f"ד/ב/ש count {c['rho_honey']:+.2f}, exciting-letter share (TABLE class E) {c['rho_exc']:+.2f}")
    print("pass: " + ", ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in c["pass"].items()))
