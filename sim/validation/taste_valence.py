"""Measured valence of each GRN group: its effect on MN9 in the simulated brain.

Run from sim/:  PYTHONPATH=src uv run python -m validation.taste_valence [screen|report]
Background = sugar LB3c at BG_RATE Hz per GRN, both sides. Each other eligible
group is added at taste_probe.SCREEN_RATE; delta = MN9(bg + group) - MN9(bg).
Excitation alone comes from the runaway screen (taste_screen.jsonl), so LB3c
(the background itself) is scored by that. Literature valence (VALENCE, by GRN
sub-class) is shown only as a cross-check.
"""
import sys
from collections import defaultdict

import numpy as np

from borer_sim import data, taste
from validation.runner import load
from validation.taste_probe import SCREEN_RATE, SCREEN_SEEDS, run

SUGAR, BG_RATE = "sugar:LB3c", 75.0
FILE = "taste_valence.jsonl"
VALENCE = {  # labellar taste literature; any other sub-class: neutral
    "sugar": "attractive", "sugar/low_salt": "attractive", "water": "attractive",
    "putative_attractive": "attractive", "bitter": "aversive",
    "high_salt/heavy_metal": "aversive", "putative_aversive": "aversive",
}


def _groups() -> dict:
    return {name: (VALENCE.get(name.split(":")[0], "neutral"), ids)
            for name, ids in taste.groups().items()}


def screen():
    groups = _groups()
    bg = [(data.to_index(groups[SUGAR][1]), BG_RATE)]
    jobs = {f"bg|{s}": (bg, s) for s in SCREEN_SEEDS}
    jobs |= {f"{name}|{s}": (bg + [(data.to_index(ids), SCREEN_RATE)], s)
             for name, (_, ids) in groups.items() if name != SUGAR for s in SCREEN_SEEDS}
    run(FILE, jobs)


def measured() -> dict[str, tuple[float, float, float]]:
    """group -> (MN9 alone, delta on sugar background, seed sd of the delta run)."""
    def by(name):
        out = defaultdict(list)
        for key, m in load(name).items():
            out[key.split("|")[0]].append(sum(m["MN9"]))
        return out
    alone, val = by("taste_screen.jsonl"), by(FILE)
    base = float(np.mean(val["bg"]))
    return {g: (float(np.mean(alone[g])), float(np.mean(val[g])) - base if g in val else np.nan,
                float(np.std(val[g])) if g in val else np.nan) for g in _groups()}


def report():
    vals = load(FILE)
    base = np.mean([sum(vals[f"bg|{s}"]["MN9"]) for s in SCREEN_SEEDS])
    print(f"Background {SUGAR} at {BG_RATE:g} Hz: MN9 {base:.1f} Hz\n")
    print("| GRN group | GRNs | MN9 alone | delta on sugar bg (sd) | literature |\n|---|---|---|---|---|")
    groups = _groups()
    for g, (a, d, sd) in sorted(measured().items(), key=lambda kv: -np.nan_to_num(kv[1][1], nan=1e9)):
        print(f"| {g} | {len(groups[g][1])} | {a:.1f} | {d:+.1f} ({sd:.1f}) | {groups[g][0]} |")


if __name__ == "__main__":
    {"screen": screen, "report": report}[sys.argv[1]]()
