"""Tabulate prototypes A and B (validation.proto_probe) as markdown.

Run from sim/:  PYTHONPATH=src uv run python -m validation.proto_report a|b
Readouts: every cell_class|side population, MN9 (CB0701) and DNa02.
Pass: (a) one direction (ipsi or contra) in >= 90% of one-side runs at
the top level; (b) that side's activity strictly rises over the levels
and is > 0 at the lowest; (c) flip rate >= 75% with >= 80% decided.
Runaway = a run with > RUNAWAY active neurons.
"""
import sys
from collections import defaultdict

import numpy as np

from validation.steering_report import load, winner

OPP = {"left": "right", "right": "left"}
RUNAWAY = 4000
INPUTS = {"a1": "olfactory", "a2": "olfactory", "b": "gustatory"}  # driven class: reference only


def value(m, readout, side):
    if readout in ("MN9", "DNa02"):
        return m[readout][0 if side == "left" else 1]
    return m["pop"].get(f"{readout}|{side}", 0.0)


def readouts(*results):
    keys = {k.split("|")[0] for res in results for m in res.values() for k in m["pop"]}
    pops = [c for c in keys if any(f"{c}|left" in m["pop"] for r in results for m in r.values())]
    return ["MN9", "DNa02"] + sorted(pops)


def side_grade(res, readout):
    by = defaultdict(list)
    for key, m in res.items():
        lvl, _, side, _ = key.split("|")
        by[float(lvl)].append((value(m, readout, side), value(m, readout, OPP[side])))
    levels = sorted(by)
    top = np.array(by[levels[-1]])
    p = float(np.mean(top[:, 0] > top[:, 1]))
    q = float(np.mean(top[:, 0] < top[:, 1]))
    ipsi = p >= q
    col = 0 if ipsi else 1
    grade = [float(np.mean([r[col] for r in by[lvl]])) for lvl in levels]
    graded = grade[0] > 0 and all(a < b for a, b in zip(grade, grade[1:]))
    return ("ipsi" if ipsi else "contra"), max(p, q), grade, graded


def flips(res, readout):
    runs = defaultdict(dict)
    for key, m in res.items():
        x, y, order, seed = key.split("|")
        runs[x, y][order, seed] = value(m, readout, "left") - value(m, readout, "right")
    f = d = n = 0
    for (x, y), r in runs.items():
        for seed in {s for _, s in r}:
            n += 1
            w1, w2 = winner(r["XY", seed], x, y), winner(r["YX", seed], y, x)
            if w1 and w2:
                d += 1
                f += w1 == w2
    return f, d, n


def main(proto):
    side, swap = load(f"proto_{proto}_side.jsonl"), load(f"proto_{proto}_swap.jsonl")
    act = np.array([m["active"] for m in list(side.values()) + list(swap.values())])
    print(f"Runs {len(act)}; active median {np.median(act):.0f}, max {act.max():,}; "
          f"runaway (> {RUNAWAY:,} active): {(act > RUNAWAY).sum()}/{len(act)}\n")
    print("| Readout | direction | side ok | levels (dominant side) | graded | flips | decided | verdict |\n"
          "|---|---|---|---|---|---|---|---|")
    rows = []
    for r in readouts(side, swap):
        direction, ok, grade, graded = side_grade(side, r)
        f, d, n = flips(swap, r)
        if not any(grade) and d == 0:
            continue
        flip = f / d if d else 0.0
        verdict = ("input (ref)" if r == INPUTS.get(proto) else
                   "PASS" if ok >= 0.9 and graded and flip >= 0.75 and d >= 0.8 * n else "fail")
        rows.append((verdict != "fail", flip, r, direction, ok, grade, graded, f, d, n, verdict))
    for _, flip, r, direction, ok, grade, graded, f, d, n, verdict in sorted(rows, reverse=True):
        g = " → ".join(f"{x:.1f}" for x in grade)
        print(f"| {r} | {direction} | {ok:.0%} | {g} | {'yes' if graded else 'no'} | "
              f"{f}/{d} ({flip:.0%}) | {d}/{n} | {verdict} |")


if __name__ == "__main__":
    main(sys.argv[1])
