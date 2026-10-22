"""Mood probes (P1-7/P1-8, SIM_VERSION 0.7.0).

Run from sim/:  PYTHONPATH=src:. uv run python -m validation.mood_probe noise|report-noise
noise: background-noise scan — 4 OLD+NEW arguments (lowest, median, P90, highest
no-mood MN9) × NOISE_HZ (at MOOD["noise_mv"]) × 2 seeds, plus hunger 1 without
noise; records MN9 readout bins and GF spikes (does arousal ever make GF fire?).
"""
import sys

import numpy as np

from borer_sim import readout, taste
from borer_sim.mood import Mood, tasting
from borer_sim.params import MOOD, TASTING_MS
from validation.runner import RUNAWAY, load, run_jobs
from validation.sugar_mn9 import OUT
from validation.taste_criteria import tastings
from validation.taste_spam import NATURAL

NOISE_HZ = (0.0, 10.0, 20.0, 30.0, 50.0, 100.0, 300.0)
NOISE_FILE = f"mood_noise_{MOOD['noise_mv']:g}mv.jsonl"


def extra(res) -> dict:
    return {"mn9_bins": readout.mn9_bins(res).tolist(),
            "gf_spikes": int(res.counts[readout._both(readout.anatomy.giant_fiber)].sum())}


def _picks() -> list[int]:
    mean = {i: np.mean([v[0] for v in d.values()])
            for i, d in tastings(load("taste_v6_natural_1500ms_b2.jsonl")).items()}
    order = sorted(mean, key=mean.get)
    return [order[0], order[len(order) // 2], order[int(0.9 * len(order))], order[-1]]


def noise():
    jobs = {}
    for i in _picks():
        for s in (783, 784):
            for hz in NOISE_HZ:
                jobs[f"{i}|{s}|h0|{hz:g}"] = (taste.tasting(NATURAL[i]), s, hz)
            jobs[f"{i}|{s}|h1|0"] = (tasting(NATURAL[i], Mood(1.0, 0.0)), s, 0.0)
    print(f"{NOISE_FILE}: {len(jobs)} jobs", flush=True)
    run_jobs(jobs, OUT / NOISE_FILE, TASTING_MS, extra=extra)
    report_noise()


def report_noise():
    """Per level: MN9 / active / GF per tasting, and flips / gap over the 6 pairs x 2 seeds."""
    res = load(NOISE_FILE)
    picks, seeds = sorted({int(k.split("|")[0]) for k in res}), ("783", "784")
    print("| mood | MN9 Hz per arg (seed 783) | max active | GF spikes | flips median (max) "
          "| gap median |\n|---|---|---|---|---|---|")
    for h, hz in [("h0", f"{x:g}") for x in NOISE_HZ] + [("h1", "0")]:
        r = {(i, s): res[f"{i}|{s}|{h}|{hz}"] for i in picks for s in seeds}
        hm = [readout.metrics(r[a, s]["mn9_bins"], r[b, s]["mn9_bins"], TASTING_MS / 1000)
              for s in seeds for n, a in enumerate(picks) for b in picks[n + 1:]]
        act = max(m["active"] for m in r.values())
        print(f"| {'hunger 1' if h == 'h1' else f'noise {hz} Hz'} | "
              f"{' / '.join(f'{sum(r[i, seeds[0]]["MN9"]):.1f}' for i in picks)} | "
              f"{act}{' RUNAWAY' if act > RUNAWAY else ''} | {sum(m['gf_spikes'] for m in r.values())} | "
              f"{np.median([m['direction_flips'] for m in hm]):g} ({max(m['direction_flips'] for m in hm)}) | "
              f"{np.median([m['gap'] for m in hm]):.2f} |")


if __name__ == "__main__":
    {"noise": noise, "report-noise": report_noise}[sys.argv[1]](*sys.argv[2:])
