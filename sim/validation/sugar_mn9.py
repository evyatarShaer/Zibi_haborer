"""P1-3: reproduce Shiu et al. 2024 Fig. 1/3 — sugar GRNs drive MN9.

Run from sim/:  PYTHONPATH=src uv run python -m validation.sugar_mn9 [n_trials]

Reference: Shiu's published example output (v630, 21 sugar GRNs at
200 Hz, 30 trials) in sim/data/raw/shiu_reference/sugarR_v630.parquet.
Pass criteria are fixed in docs/POC_REPORT.md (P1-3) before running.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

from borer_sim import data
from validation import shiu_brian2

# Shiu's v630 IDs (figures.ipynb). Shiu's "right" = annotation side "left".
SUGAR_V630 = [
    720575940624963786, 720575940630233916, 720575940637568838, 720575940638202345,
    720575940617000768, 720575940630797113, 720575940632889389, 720575940621754367,
    720575940621502051, 720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940620900446, 720575940617937543, 720575940632425919,
    720575940633143833, 720575940612670570, 720575940628853239, 720575940629176663,
    720575940611875570,
]
BITTER_V630 = [
    720575940621778381, 720575940602353632, 720575940617094208, 720575940619197093,
    720575940626287336, 720575940618600651, 720575940627692048, 720575940630195909,
    720575940646212996, 720575940610483162, 720575940645743412, 720575940627578156,
    720575940622298631, 720575940621008895, 720575940629146711, 720575940610259370,
    720575940610481370, 720575940619028208, 720575940614281266, 720575940613061118,
    720575940604027168,
]
# MN9 pair (cell_type CB0701). First id is Shiu's id_mn9; partner found via cell_type.
MN9 = {"mn9_shiu": 720575940660219265, "mn9_partner": 720575940618238523}
REFERENCE = {"mn9_shiu": 93.27, "mn9_partner": 61.80, "active": 448}  # v630, 200 Hz
TOLERANCE = 0.30
SEED = 783
OUT = Path(__file__).resolve().parents[1] / "data" / "processed" / "validation"


def present(ids):
    known = set(data.neuron_ids())
    return [r for r in ids if r in known]


def summarize(counts):
    mn9 = data.to_index(list(MN9.values()))
    rates = counts.mean(0)  # 1 s trials → Hz
    return {name: round(float(rates[i]), 2) for name, i in zip(MN9, mn9)} | {
        "active": round(float((counts > 0).sum(1).mean()), 1),
        "total_spikes": round(float(counts.sum(1).mean()), 1),
    }


def checks(res, repeat_identical):
    s, sb, b, base = res["sugar200"], res["sugar200+bitter200"], res["bitter200"], res["baseline"]
    within = lambda k: abs(s[k] - REFERENCE[k]) <= TOLERANCE * REFERENCE[k]
    return {
        "determinism (same seed → identical counts)": repeat_identical,
        "baseline: no spikes": base["total_spikes"] == 0,
        "sugar: MN9 (Shiu id) within ±30% of v630": within("mn9_shiu"),
        "sugar: MN9 partner within ±30% of v630": within("mn9_partner"),
        "sugar: active neurons within ±30% of v630": within("active"),
        "bitter alone: MN9 silent": b["mn9_shiu"] == 0 and b["mn9_partner"] == 0,
        "bitter suppresses sugar → MN9": sb["mn9_shiu"] < s["mn9_shiu"],
    }


def conditions():
    """The four P1-3 conditions as {name: drives}."""
    si, bi = data.to_index(present(SUGAR_V630)), data.to_index(present(BITTER_V630))
    return {
        "baseline": [],
        "sugar200": [(si, 200)],
        "bitter200": [(bi, 200)],
        "sugar200+bitter200": [(si, 200), (bi, 200)],
    }


def main(n_trials):
    sugar, bitter = present(SUGAR_V630), present(BITTER_V630)
    conds = conditions()
    res, timing, counts = {}, {}, {}
    for name, drives in conds.items():
        t = time.time()
        counts[name] = shiu_brian2.run_trials(drives, n_trials, SEED)
        timing[name] = round(time.time() - t, 1)
        res[name] = summarize(counts[name])
        print(name, res[name], f"{timing[name]} s", flush=True)
    repeat = shiu_brian2.run_trials(conds["sugar200"], 2, SEED)
    ok = checks(res, bool(np.array_equal(repeat, counts["sugar200"][:2])))

    OUT.mkdir(parents=True, exist_ok=True)
    report = {"n_trials": n_trials, "seed": SEED, "n_sugar": len(sugar),
              "n_bitter": len(bitter), "reference_v630": REFERENCE,
              "results": res, "seconds_per_condition": timing, "checks": ok}
    (OUT / "sugar_mn9.json").write_text(json.dumps(report, indent=2))
    for k, v in ok.items():
        print(("PASS " if v else "FAIL ") + k)
    return all(ok.values())


if __name__ == "__main__":
    sys.exit(0 if main(int(sys.argv[1]) if len(sys.argv) > 1 else 30) else 1)
