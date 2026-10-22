"""Outcome calibration on OLD+NEW with mood sampled as the product would (P1-7/P1-8).

Run from sim/:  PYTHONPATH=src:. uv run python -m validation.mood_calib run|report
run: the 60 OLD+NEW probe pairs x 10 cases. Case c of pair p: simulation seed SEEDS[c]
(the no-mood run's seed, for a paired comparison), mood = mood.from_case(case seed, wait),
case seed = CASE0 + 100 p + c, wait ~ Exponential(WAIT_MEAN_H) h from the case seed
(assumption: no product data on waiting yet). Both tastings: same seed, same mood.
report: outcome mix at params.OUTCOME, the threshold grid, and verdict changes vs no mood.
Selection rule (fixed before running): a threshold set passes if Win >= 50%, every
special outcome <= 15%, and every outcome that can occur (Fled only if GF ever fired)
occurs at least once. Keep the SPEC defaults if they pass; else the passing set with
the fewest thresholds changed, then the smallest summed relative change.
"""
import sys
from collections import Counter
from itertools import product

import numpy as np

from borer_sim import mood, readout
from borer_sim.params import OUTCOME, TASTING_MS
from validation.mood_probe import extra
from validation.runner import load, run_jobs
from validation.sugar_mn9 import OUT
from validation.taste_probe import SEEDS
from validation.taste_spam import NATURAL, NATURAL_PAIRS

CASE0, WAIT_MEAN_H, WAIT_STREAM = 10_000, 2.0, 0x77616974
FILE = "mood_calib_1500ms.jsonl"
NO_MOOD = "taste_v6_natural_1500ms_b2.jsonl"
GRID = {"tie_gap": (0.03, 0.05, 0.08, 0.10, 0.15), "froze_hz": (2.0, 4.0, 6.0, 8.0),
        "food_hunger": (0.6, 0.7, 0.8), "dither_flips": (2, 3, 4, 5, 6, 8, 10)}
SPECIAL = ("fled", "froze", "food", "dithered", "tie")


def case(p: int, c: int) -> tuple[int, mood.Mood]:
    seed = CASE0 + 100 * p + c
    wait = float(np.random.default_rng((seed, WAIT_STREAM)).exponential(WAIT_MEAN_H))
    return seed, mood.from_case(seed, wait)


def run():
    jobs = {}
    for p, (a, b) in enumerate(NATURAL_PAIRS):
        for c, s in enumerate(SEEDS):
            m = case(p, c)[1]
            for side, i in (("a", a), ("b", b)):
                jobs[f"{p}|{c}|{side}"] = (mood.tasting(NATURAL[i], m), s, m.noise_hz)
    print(f"{FILE}: {len(jobs)} jobs", flush=True)
    run_jobs(jobs, OUT / FILE, TASTING_MS, extra=extra)
    report()


def hearings() -> list[dict]:
    res, sec = load(FILE), TASTING_MS / 1000
    out = []
    for p in range(len(NATURAL_PAIRS)):
        for c in range(len(SEEDS)):
            ta, tb = res[f"{p}|{c}|a"], res[f"{p}|{c}|b"]
            m = readout.metrics(ta["mn9_bins"], tb["mn9_bins"], sec)
            m |= {"giant_fiber_fired": ta["gf_spikes"] + tb["gf_spikes"] > 0, "p": p, "c": c,
                  "mood": case(p, c)[1], "active": max(ta["active"], tb["active"])}
            out.append(m)
    return out


def mix(hs, th: dict) -> Counter:
    saved = dict(OUTCOME)
    OUTCOME.update(th)  # validation override of the single threshold table
    try:
        return Counter(readout.outcome(h, h["mood"].hunger) for h in hs)
    finally:
        OUTCOME.update(saved)


def passes(cnt: Counter, n: int, fled_possible: bool) -> bool:
    need = [o for o in SPECIAL if o != "fled" or fled_possible]
    return (cnt["win"] >= 0.5 * n and all(cnt[o] <= 0.15 * n for o in SPECIAL)
            and all(cnt[o] > 0 for o in need))


def choose(hs) -> dict:
    fled_possible = any(h["giant_fiber_fired"] for h in hs)
    default = {k: OUTCOME[k] for k in GRID}
    ok = [dict(zip(GRID, v)) for v in product(*GRID.values())
          if passes(mix(hs, dict(zip(GRID, v))), len(hs), fled_possible)]
    if not ok:
        return {}
    return min(ok, key=lambda t: (sum(t[k] != default[k] for k in t),
                                  sum(abs(t[k] / default[k] - 1) for k in t)))


def _verdict(o: str, m: dict) -> str:
    return f"win {m['winner']}" if o == "win" else o


def _table(title: str, cnt: Counter, n: int):
    print(f"\n{title}\n| outcome | hearings | share |\n|---|---|---|")
    for o in readout.OUTCOMES:
        print(f"| {o} | {cnt[o]} | {cnt[o] / n:.1%} |")


def changes(hs, th: dict):
    """Verdict with mood vs the no-mood tasting pair (same seed, no hunger, no noise)."""
    from validation.taste_criteria import tastings
    nm, sec, saved = tastings(load(NO_MOOD)), TASTING_MS / 1000, dict(OUTCOME)
    OUTCOME.update(th)
    rows = []
    for h in hs:
        a, b = NATURAL_PAIRS[h["p"]]
        s = str(SEEDS[h["c"]])
        x = readout.metrics([nm[a][s][0] * sec], [nm[b][s][0] * sec], sec)
        x |= {"giant_fiber_fired": False, "direction_flips": 0}
        rows.append((_verdict(readout.outcome(x, 0.0), x), _verdict(readout.outcome(h, h["mood"].hunger), h), h))
    OUTCOME.update(saved)
    changed = [r for r in rows if r[0] != r[1]]
    both = [r for r in rows if r[0].startswith("win") and r[1].startswith("win")]
    flip = sum(r[0] != r[1] for r in both)
    print(f"\nverdict changed by mood: {len(changed)}/{len(rows)} ({len(changed) / len(rows):.1%}); "
          f"winner flipped where both decided: {flip}/{len(both)} ({flip / len(both):.1%})")
    print(f"changes: {dict(Counter(f'{x} -> {y}' for x, y, _ in changed).most_common(8))}")
    for name in ("arousal", "hunger"):
        v = np.array([getattr(r[2]["mood"], name) for r in rows])
        cuts = np.quantile(v, [1 / 3, 2 / 3])
        for k, (lo, hi) in enumerate(zip([-1, *cuts], [*cuts, 2])):
            sel = [r for r, x in zip(rows, v) if lo < x <= hi]
            print(f"  {name} tercile {k + 1} ({lo if lo >= 0 else 0:.2f}-{min(hi, 1):.2f}]: "
                  f"changed {sum(r[0] != r[1] for r in sel)}/{len(sel)}")


def report():
    hs = hearings()
    n = len(hs)
    hunger = np.array([h["mood"].hunger for h in hs])
    print(f"{n} hearings; hunger median {np.median(hunger):.2f}, > 0.8 in {np.mean(hunger > 0.8):.1%}; "
          f"GF fired in {sum(h['giant_fiber_fired'] for h in hs)}; "
          f"runaway (> 4,000 active) in {sum(h['active'] > 4000 for h in hs)}; "
          f"flips median {np.median([h['direction_flips'] for h in hs]):g}")
    default = {k: OUTCOME[k] for k in GRID}
    _table(f"SPEC defaults {default}", mix(hs, default), n)
    best = choose(hs)
    print(f"\nchosen (rule in docstring): {best or 'NO THRESHOLD SET PASSES'}")
    if best:
        _table(f"chosen {best}", mix(hs, best), n)
        for k, values in GRID.items():
            print(f"  vary {k}: " + "; ".join(
                f"{v:g} -> " + " ".join(f"{o} {c}" for o, c in sorted(mix(hs, best | {k: v}).items()))
                for v in values))
    changes(hs, best or default)


if __name__ == "__main__":
    {"run": run, "report": report}[sys.argv[1]]()
