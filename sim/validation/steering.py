"""Steering readout + resumable parallel runner for the P1-6 steering probe.

Workers are forked after the model is built, so they share its memory.
Results append to a JSONL file; finished job keys are skipped on rerun.
Steering index SI = (L - R) / (L + R) on DNa02 rates; SI > 0 = turn left
(DNa02 drives ipsilateral turning).
"""
import json
import multiprocessing as mp
import os
from functools import cache
from pathlib import Path

import numpy as np
import torch

from borer_sim import anatomy
from borer_sim.model import Model

CANDIDATE_DNS = ["DNa01", "DNa03", "DNa04", "DNa11", "DNb05", "DNb06", "DNg13", "DNp09", "DNb02"]
DURATION_MS = 1000

_model = None
_metric = None


@cache
def _dn_sets():
    sets = {"DNa02": {s: anatomy.turning_dns(s) for s in anatomy.SIDES},
            "GF": {s: anatomy.giant_fiber(s) for s in anatomy.SIDES}}
    for name in CANDIDATE_DNS:
        sets[name] = {s: anatomy.cell_type(name, s) for s in anatomy.SIDES}
    return sets


def steering_index(left: float, right: float) -> float:
    return (left - right) / (left + right) if left + right else 0.0


def metrics(counts) -> dict:
    """Readout from per-neuron spike counts of a 1 s run (counts = Hz)."""
    out = {"active": int((counts > 0).sum())}
    for name, sides in _dn_sets().items():
        left, right = (float(counts[sides[s]].mean()) for s in anatomy.SIDES)
        out[name] = [left, right]
    out["si"] = steering_index(*out["DNa02"])
    return out


def _work(job):
    key, drives, seed, threads = job
    torch.set_num_threads(threads)
    return key, _metric(_model.run(drives, DURATION_MS, seed).counts)


def run_jobs(jobs: dict, out: Path, workers: int, threads: int, metric=metrics) -> dict:
    """jobs: {key: (drives, seed)}. Returns {key: metric(counts)}, incl. earlier results.

    `metric` must be warmed (its caches filled) here, before the fork."""
    global _model, _metric
    _metric = metric
    done = {}
    if out.exists():
        done = {r["key"]: r["m"] for r in map(json.loads, out.read_text().splitlines())}
    todo = [(k, d, s, threads) for k, (d, s) in jobs.items() if k not in done]
    if todo:
        _model = _model or Model.from_connectome()
        metric(np.zeros(_model.n, dtype=np.int32))  # warm caches pre-fork (no torch op)
        with mp.get_context("fork").Pool(workers) as pool, open(out, "a") as f:
            for i, (key, m) in enumerate(pool.imap_unordered(_work, todo, chunksize=1), 1):
                done[key] = m
                f.write(json.dumps({"key": key, "m": m}) + "\n")
                f.flush()
                if i % 50 == 0 or i == len(todo):
                    print(f"  {out.name}: {i}/{len(todo)} new", flush=True)
    return {k: done[k] for k in jobs}


def cpu_count() -> int:
    return len(os.sched_getaffinity(0))
