"""P1-5 performance: load/build time, per-run wall-clock, peak RSS.

One process per thread count (torch threads can't be changed cleanly):
    PYTHONPATH=src uv run python -m validation.bench <threads>
Appends one JSON line per thread count to data/processed/validation/bench.jsonl.
"""
import json
import resource
import statistics
import sys
import time

import torch

from borer_sim import anatomy, data
from borer_sim.model import Model
from validation.sugar_mn9 import OUT, conditions

RUNS = 5
DURATIONS_MS = (1000, 2000)


def timed(fn):
    t = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t


def main(threads):
    torch.set_num_threads(threads)
    _, load_s = timed(data.edges)
    model, build_s = timed(Model.from_connectome)
    drives = {
        "sugar200": conditions()["sugar200"],
        "orn_V_L+DA2_R_100": [(anatomy.orns("V", "left"), 100),
                              (anatomy.orns("DA2", "right"), 100)],
    }
    model.run(drives["sugar200"], 100, seed=0)  # warm-up
    runs = {}
    for name, d in drives.items():
        for ms in DURATIONS_MS:
            times = [timed(lambda k=k: model.run(d, ms, seed=k))[1] for k in range(RUNS)]
            runs[f"{name} {ms} ms"] = round(statistics.median(times), 2)
    row = {"threads": threads, "load_s": round(load_s, 2), "build_s": round(build_s, 2),
           "median_run_s": runs,
           "peak_rss_gb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2)}
    print(json.dumps(row))
    with open(OUT / "bench.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]))
