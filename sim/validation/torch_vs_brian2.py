"""P1-5: borer_sim.model vs the Brian2 port on the four P1-3 conditions.

Run from sim/ after validation.sugar_mn9 (its JSON is the Brian2 reference):
    PYTHONPATH=src uv run python -m validation.torch_vs_brian2 [n_trials]
Pass: MN9 rates within ±10% and active neurons within ±15% of Brian2
(a Brian2 value of 0 must be matched exactly); bitter suppresses MN9.
"""
import json
import sys
import time

import numpy as np
import torch

from borer_sim import data
from borer_sim.model import Model
from validation.sugar_mn9 import MN9, OUT, SEED, conditions, summarize

TOL = {"mn9_shiu": 0.10, "mn9_partner": 0.10, "active": 0.15}
THREADS = 2  # production server cores


def within(value, ref, tol):
    return value == 0 if ref == 0 else abs(value - ref) <= tol * ref


def main(n_trials):
    torch.set_num_threads(THREADS)
    brian = json.loads((OUT / "sugar_mn9.json").read_text())["results"]
    model = Model.from_connectome()
    mn9 = data.to_index(list(MN9.values()))
    res, checks = {}, {}
    for name, drives in conditions().items():
        t = time.time()
        counts = np.stack([model.run(drives, 1000, SEED + k).counts for k in range(n_trials)])
        se = counts[:, mn9].std(0, ddof=1) / np.sqrt(n_trials)
        res[name] = summarize(counts) | {"mn9_se": se.round(2).tolist(),
                                          "seconds": round(time.time() - t, 1)}
        for key, tol in TOL.items():
            checks[f"{name}: {key} within ±{tol:.0%}"] = within(res[name][key], brian[name][key], tol)
        print(name, res[name], "| brian2", brian[name], flush=True)
    checks["bitter suppresses sugar → MN9"] = (
        res["sugar200+bitter200"]["mn9_shiu"] < res["sugar200"]["mn9_shiu"])

    report = {"n_trials": n_trials, "seed": SEED, "threads": THREADS,
              "torch": res, "brian2": brian, "checks": checks}
    (OUT / "torch_vs_brian2.json").write_text(json.dumps(report, indent=2))
    for k, v in checks.items():
        print(("PASS " if v else "FAIL ") + k)
    return all(checks.values())


if __name__ == "__main__":
    sys.exit(0 if main(int(sys.argv[1]) if len(sys.argv) > 1 else 30) else 1)
