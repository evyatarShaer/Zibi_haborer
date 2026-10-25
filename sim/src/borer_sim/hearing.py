"""Product hearing (SPEC §6, §14): two arguments + a hearing seed → verdict + brain summary.

The seed gives the mood (mood.product) and drives both tastings. The tastings run in
parallel, 2 processes × 1 thread, in workers forked after the model is built (they
share its memory). The brain summary is group-level only, never per letter (SPEC §2.3).
"""
import multiprocessing as mp
import platform
import time

import torch

from borer_sim import mood, readout, taste
from borer_sim.model import Model, Result
from borer_sim.params import OUTCOME, TASTING_MS
from borer_sim.version import SIM_VERSION

PLATFORM = f"{platform.platform()} | {platform.python_version()} | torch {torch.__version__}"

_model = None


def _tasting(job) -> Result:
    drives, seed, noise_hz, ms = job
    torch.set_num_threads(1)
    return _model.run(drives, ms, seed, noise_hz)


def workers(model: Model):
    """Pool of the two tasting processes, forked with `model`; use as a context manager."""
    global _model
    _model = model
    return mp.get_context("fork").Pool(2)


def taste_both(pool, drives_a, drives_b, seed: int, noise_hz: float,
               ms: float = TASTING_MS) -> tuple[Result, Result]:
    """Both tastings at once, same seed and noise."""
    jobs = [(drives_a, seed, noise_hz, ms), (drives_b, seed, noise_hz, ms)]
    return tuple(pool.map(_tasting, jobs, chunksize=1))


def brain(res_a: Result, res_b: Result, m: mood.Mood, seed: int, ms: float) -> dict:
    """Stored "what happened in the brain?" summary: MN9 Hz per readout bin and mean GRN Hz
    per taste class, for each tasting; mood, seed, version, platform."""
    bin_s, sec = OUTCOME["readout_bin_ms"] / 1000, ms / 1000
    return {"bin_ms": OUTCOME["readout_bin_ms"],
            "mn9_hz": [(readout.mn9_bins(r) / bin_s).tolist() for r in (res_a, res_b)],
            "taste_hz": [{c: float(r.counts[idx].mean() / sec) for c, idx in taste.classes().items()}
                         for r in (res_a, res_b)],
            "mood": {"hunger": m.hunger, "arousal": m.arousal}, "seed": seed,
            "sim_version": SIM_VERSION, "platform": PLATFORM}


def run(pool, text_a: str, text_b: str, seed: int, ms: float = TASTING_MS) -> dict:
    """One hearing: mood, metrics + outcome, brain summary, wall-clock."""
    start, m = time.perf_counter(), mood.product(seed)
    res = taste_both(pool, mood.tasting(text_a, m), mood.tasting(text_b, m), seed, m.noise_hz, ms)
    return {"seed": seed, "mood": {"hunger": m.hunger, "arousal": m.arousal},
            "metrics": readout.verdict(*res, m, ms / 1000), "brain": brain(*res, m, seed, ms),
            "sim_version": SIM_VERSION, "platform": PLATFORM,
            "duration_ms": round((time.perf_counter() - start) * 1000)}

