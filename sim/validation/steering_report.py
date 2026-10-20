"""Tabulate the steering probe (validation.steering_probe) as markdown.

Run from sim/:  PYTHONPATH=src uv run python -m validation.steering_report
Toward score T = (mean SI stimulating left - mean SI stimulating right) / 2;
T > 0 = the model turns toward the stimulated side. Model direction is
"toward"/"away" when >= 5 of 6 runs share T's sign, else "unclear".
"""
import json
from collections import defaultdict

import numpy as np

from borer_sim import anatomy, smell
from validation import steering
from validation.sugar_mn9 import OUT

VALENCE = {g: (l, v) for l, (g, v) in smell.LETTERS.items()} | {
    "V": ("!", smell.AVERSIVE), "DA2": ("?", smell.AVERSIVE)}


def load(name):
    return {r["key"]: r["m"] for r in map(json.loads, (OUT / name).read_text().splitlines())}


def toward(runs, metric="si"):
    """Per-run toward values: SI on left-side runs, -SI on right-side runs."""
    def si(m):
        return m["si"] if metric == "si" else steering.steering_index(*m[metric])
    return np.array([si(m) if side == "left" else -si(m) for side, m in runs])


def direction(tw):
    t = tw.mean()
    agree = int((np.sign(tw) == np.sign(t)).sum()) if t else 0
    return ("toward" if t > 0 else "away") if agree >= 5 else "unclear", agree


def glomerulus_table(res):
    by = defaultdict(list)
    for key, m in res.items():
        g, lvl, side, _ = key.split("|")
        by[g, lvl].append((side, m))
    t = anatomy.orn_glomeruli()
    rows, dirs = [], {}
    print("| Glom | ORNs L/R | Letter | Lit. valence | T low | T mid | T high | SD mid | "
          "SNR mid | agree mid | mirror mid | active mid | GF Hz high | model |")
    print("|" + "---|" * 14)
    for g in sorted({g for g, _ in by}):
        tw = {lvl: toward(by[g, lvl]) for lvl in ("low", "mid", "high")}
        mid = by[g, "mid"]
        sl = np.mean([m["si"] for s, m in mid if s == "left"])
        sr = np.mean([m["si"] for s, m in mid if s == "right"])
        sd = tw["mid"].std(ddof=1)
        snr = abs(tw["mid"].mean()) / sd if sd else float("inf")
        d, agree = direction(tw["mid"])
        dirs[g] = d
        gf = np.mean([sum(m["GF"]) for _, m in by[g, "high"]])
        act = np.mean([m["active"] for _, m in mid])
        letter, val = VALENCE.get(g, ("", "—"))
        print(f"| {g} | {t.loc[g, 'left']}/{t.loc[g, 'right']} | {letter} | {val} | "
              f"{tw['low'].mean():+.2f} | {tw['mid'].mean():+.2f} | {tw['high'].mean():+.2f} | "
              f"{sd:.2f} | {snr:.1f} | {agree}/6 | {sl + sr:+.2f} | {act:.0f} | {gf:.1f} | {d} |")
        rows.append((g, val, d))
    return by, rows


def confusion(rows):
    print("\n| Literature \\ model | toward | away | unclear |\n|---|---|---|---|")
    for val in (smell.ATTRACTIVE, smell.AVERSIVE, smell.NEUTRAL, "—"):
        c = [sum(1 for _, v, d in rows if v == val and d == x) for x in ("toward", "away", "unclear")]
        print(f"| {val} | {c[0]} | {c[1]} | {c[2]} |")


def candidate_dns(by):
    print("\n| DN | mean toward (mid) | glomeruli agreeing with DNa02 sign |\n|---|---|---|")
    gloms = sorted({g for g, _ in by})
    for dn in steering.CANDIDATE_DNS:
        tws = [toward(by[g, "mid"], dn).mean() for g in gloms]
        ref = [toward(by[g, "mid"]).mean() for g in gloms]
        agree = sum(np.sign(a) == np.sign(b) and b != 0 for a, b in zip(tws, ref))
        print(f"| {dn} | {np.mean(tws):+.2f} | {agree}/{len(gloms)} |")


def winner(si, left_text, right_text):
    return left_text if si > 0 else right_text if si < 0 else None


def pairs_table(res, title):
    by = defaultdict(dict)
    for key, m in res.items():
        x, y, order, seed = key.split("|")
        by[x, y][order, seed] = m
    flips = decided = 0
    print(f"\n**{title}**\n\n| X (left first) | Y | X wins | flips | decided | mean SI XY | "
          f"mean SI YX | active |\n|---|---|---|---|---|---|---|---|")
    for (x, y), runs in by.items():
        seeds = sorted({s for _, s in runs})
        f = d = xw = 0
        for s in seeds:
            w1 = winner(runs["XY", s]["si"], x, y)
            w2 = winner(runs["YX", s]["si"], y, x)
            if w1 and w2:
                d += 1
                f += w1 == w2
                xw += (w1 == x) + (w2 == x)
        flips, decided = flips + f, decided + d
        si = {o: np.mean([runs[o, s]["si"] for s in seeds]) for o in ("XY", "YX")}
        act = np.mean([m["active"] for m in runs.values()])
        print(f"| {x} | {y} | {xw}/{2 * d} | {f}/{d} | {d}/{len(seeds)} | {si['XY']:+.2f} | "
              f"{si['YX']:+.2f} | {act:.0f} |")
    print(f"\nFlip rate: **{flips}/{decided} = {flips / decided:.0%}** of decided (pair, seed) cases.")


def main():
    by, rows = glomerulus_table(load("steering_glomeruli.jsonl"))
    confusion(rows)
    candidate_dns(by)
    pairs_table(load("steering_pairs.jsonl"), "Competition, full input")
    pairs_table(load("steering_pairs_low.jsonl"), "Competition, x0.1 input")


if __name__ == "__main__":
    main()
