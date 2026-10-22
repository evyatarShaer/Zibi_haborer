"""Resumable parallel runner + taste readout for the validation probes.

Workers are forked after the model is built, so they share its memory.
Results append to a JSONL file; finished job keys are skipped on rerun.
Each record also logs its start time ("t0", ISO) and wall-clock ("wall_s").
Metrics always see rates in Hz (counts / seconds), whatever the duration.
"""
import json
import multiprocessing as mp
import os
import time
from datetime import datetime
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from borer_sim import anatomy, data
from borer_sim.model import Model
from validation.sugar_mn9 import OUT

# workers x threads <= 6 cores AND workers x 2.5 GB <= free RAM; env override for lighter
# loads (the Windows host stalls the VM under sustained 6-core load, POC_REPORT)
WORKERS = int(os.environ.get("BORER_WORKERS", 3))
THREADS = int(os.environ.get("BORER_THREADS", 2))
RUNAWAY = 4000  # a run with more active neurons is a runaway (whole-brain cascade)

_model = None
_metric = None
_extra = None


@cache
def _groups():
    """Per-neuron population code (cell_class | side), the population names, MN9 and GF."""
    a = data.annotations().reindex(data.neuron_ids())
    cls = a["cell_class"].where(a["cell_class"] != "ALPN",
                                "ALPN_" + a["cell_sub_class"].fillna("na").str[:5])
    key = cls.fillna(a["super_class"]).fillna("na") + "|" + a["side"].fillna("na")
    codes, uniq = pd.factorize(key.to_numpy())
    return codes, list(uniq), {s: (anatomy.mn9(s), anatomy.giant_fiber(s)) for s in anatomy.SIDES}


def metrics(counts) -> dict:
    """Active neurons, MN9 and GF (Hz, [left, right]) and spike sums per population."""
    codes, uniq, sides = _groups()
    sums = np.bincount(codes, weights=counts, minlength=len(uniq))
    return {"active": int((counts > 0).sum()),
            "MN9": [float(counts[sides[s][0]].sum()) for s in anatomy.SIDES],
            "GF": [float(counts[sides[s][1]].mean()) for s in anatomy.SIDES],
            "pop": {u: float(x) for u, x in zip(uniq, sums) if x}}


def load(name) -> dict:
    return {r["key"]: r["m"] for r in map(json.loads, (OUT / name).read_text().splitlines())}


def _work(job):
    key, drives, seed, noise_hz, threads, duration_ms = job
    torch.set_num_threads(threads)
    t0, start = datetime.now().isoformat(timespec="seconds"), time.perf_counter()
    res = _model.run(drives, duration_ms, seed, noise_hz)
    m = _metric(res.counts / (duration_ms / 1000)) | (_extra(res) if _extra else {})
    return key, m, t0, round(time.perf_counter() - start, 2)


@cache
def connectome_model() -> Model:
    return Model.from_connectome()


def run_jobs(jobs: dict, out: Path, duration_ms: float, model: Model | None = None,
             workers: int = WORKERS, threads: int = THREADS, metric=metrics, extra=None) -> dict:
    """jobs: {key: (drives, seed[, noise_hz])}. Returns {key: metric(rates) | extra(Result)},
    incl. earlier results.

    `model` defaults to the whole-brain model. `metric` is warmed (its caches
    filled) here, before the fork."""
    global _model, _metric, _extra
    _metric, _extra = metric, extra
    done = {}
    if out.exists():
        done = {r["key"]: r["m"] for r in map(json.loads, out.read_text().splitlines())}
    todo = [(k, j[0], j[1], j[2] if len(j) > 2 else 0.0, threads, duration_ms)
            for k, j in jobs.items() if k not in done]
    if todo:
        _model = model if model is not None else connectome_model()
        metric(np.zeros(_model.full_n, dtype=np.int32))  # warm caches pre-fork (no torch op)
        with mp.get_context("fork").Pool(workers) as pool, open(out, "a") as f:
            for i, (key, m, t0, wall) in enumerate(pool.imap_unordered(_work, todo, chunksize=1), 1):
                done[key] = m
                f.write(json.dumps({"key": key, "m": m, "t0": t0, "wall_s": wall}) + "\n")
                f.flush()
                if i % 50 == 0 or i == len(todo):
                    print(f"  {out.name}: {i}/{len(todo)} new", flush=True)
    return {k: done[k] for k in jobs}
