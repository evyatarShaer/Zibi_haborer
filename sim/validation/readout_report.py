"""Tabulate the sub-cascade readout probe (validation.readout_probe) as markdown.

Run from sim/:  PYTHONPATH=src uv run python -m validation.readout_report
Pass (fixed before running): (a) stimulated side > opposite in >= 90% of
one-antenna runs at the threshold level; (b) stimulated-side activity
strictly rises over 1/4, 1/2, 1 x threshold and is > 0 at 1/4; (c) swap
flip rate >= 75% with >= 80% of (pair, seed) cases decided.
"""
from collections import defaultdict

import numpy as np

from borer_sim import anatomy
from validation.readout_probe import CASCADE_ACTIVE, LEVELS, SCALES, threshold_scale
from validation.steering_probe import X_TEXTS, Y_TEXTS, hearing
from validation.steering_report import load, winner

INPUT_CLASS = "olfactory"
OPP = {"left": "right", "right": "left"}


def pop(m, cls, side):
    return m["pop"].get(f"{cls}|{side}", 0.0)


def threshold_table(res):
    print("| Scale | Input spikes/s (both antennas) | Cascades | Mean active | Max active |\n|---|---|---|---|---|")
    for s in SCALES:
        ms = [(k, m) for k, m in res.items() if float(k.split("|")[0]) == s]
        pairs = {tuple(k.split("|")[1:3]) for k, _ in ms}
        inp = np.mean([sum(len(i) * r for i, r in hearing(X_TEXTS[x], Y_TEXTS[y], s))
                       for x, y in pairs])
        act = [m["active"] for _, m in ms]
        n_c = sum(a > CASCADE_ACTIVE for a in act)
        print(f"| ×{s} | {inp:,.0f} | {n_c}/{len(ms)} | {np.mean(act):,.0f} | {max(act):,} |")


def classes(*results):
    keys = {k for res in results for m in res.values() for k in m["pop"]}
    names = {k.split("|")[0] for k in keys}
    return sorted(c for c in names if f"{c}|left" in keys and f"{c}|right" in keys)


def side_and_grade(res, cls):
    by = defaultdict(list)
    for key, m in res.items():
        lvl, _, side, _ = key.split("|")
        by[float(lvl)].append((pop(m, cls, side), pop(m, cls, OPP[side])))
    top = np.array(by[1.0])
    side_ok = float(np.mean(top[:, 0] > top[:, 1])) if len(top) else 0.0
    grade = [float(np.mean([s for s, _ in by[lvl]])) for lvl in LEVELS]
    graded = grade[0] > 0 and all(a < b for a, b in zip(grade, grade[1:]))
    return side_ok, grade, graded, float(top[:, 0].mean()), float(top[:, 1].mean())


def swap(res, cls):
    runs = defaultdict(dict)
    for key, m in res.items():
        x, y, order, seed = key.split("|")
        runs[x, y][order, seed] = pop(m, cls, "left") - pop(m, cls, "right")
    flips = decided = total = 0
    for (x, y), r in runs.items():
        for seed in {s for _, s in r}:
            total += 1
            w1, w2 = winner(r["XY", seed], x, y), winner(r["YX", seed], y, x)
            if w1 and w2:
                decided += 1
                flips += w1 == w2
    return flips, decided, total


def readout_table(side_res, swap_res):
    print("\n| Population | stim / opp (Hz·neurons) | side ok | ¼ → ½ → 1 | graded | flips | "
          "decided | verdict |\n|---|---|---|---|---|---|---|---|")
    rows = []
    for cls in classes(side_res, swap_res):
        side_ok, grade, graded, st, op = side_and_grade(side_res, cls)
        f, d, n = swap(swap_res, cls)
        flip = f / d if d else 0.0
        ok = side_ok >= 0.9 and graded and flip >= 0.75 and d >= 0.8 * n
        verdict = "input (ref)" if cls == INPUT_CLASS else "PASS" if ok else "fail"
        rows.append((verdict != "fail", flip, cls, st, op, side_ok, grade, graded, f, d, n, verdict))
    for _, flip, cls, st, op, side_ok, grade, graded, f, d, n, verdict in sorted(rows, reverse=True):
        if st + op == 0 and d == 0:
            continue
        g = " → ".join(f"{x:.1f}" for x in grade)
        print(f"| {cls} | {st:.1f} / {op:.1f} | {side_ok:.0%} | {g} | {'yes' if graded else 'no'} | "
              f"{f}/{d} ({flip:.0%}) | {d}/{n} | {verdict} |")


def sugar_control(res):
    print("\n| Sugar GRNs side | MN9 L (spikes) | MN9 R (spikes) | ipsi / contra | active |\n|---|---|---|---|---|")
    for side in anatomy.SIDES:
        ms = [m for k, m in res.items() if k.startswith(side)]
        l, r = (np.mean([m["MN9"][i] for m in ms]) for i in (0, 1))
        ipsi, contra = (l, r) if side == "left" else (r, l)
        print(f"| {side} | {l:.1f} | {r:.1f} | {ipsi:.1f} / {contra:.1f} | "
              f"{np.mean([m['active'] for m in ms]):.0f} |")


def main():
    thr = load("readout_threshold.jsonl")
    threshold_table(thr)
    print(f"\nThreshold scale: **×{threshold_scale(thr)}**")
    readout_table(load("readout_side.jsonl"), load("readout_swap.jsonl"))
    sugar_control(load("readout_sugar.jsonl"))


if __name__ == "__main__":
    main()
