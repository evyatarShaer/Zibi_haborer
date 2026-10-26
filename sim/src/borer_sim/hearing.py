"""Product hearing (SPEC §6, §14): two arguments + a hearing seed → verdict + brain summary.

The seed and the real wait give the mood (mood.from_case; mood.product draws a wait for
2A and validation) and the seed drives both tastings. A side without an argument (None,
a no-show) tastes plain water: baseline GRN rates only (SPEC §8). The tastings run in
parallel, 2 processes × 1 thread. Workers are either forked after the model is built
(they share its memory; fine for a single-threaded script) or started by "forkserver",
each building its own whole-brain model (safe in a threaded server such as the API).
The brain summary holds MN9 curves and the run's identity only: no letter, GRN group or
taste class (SPEC §2.3, §15.7).
"""
import multiprocessing as mp
import platform
import time

import torch

from borer_sim import mood, readout
from borer_sim.model import Model, Result
from borer_sim.params import OUTCOME, TASTING_MS
from borer_sim.version import SIM_VERSION

PLATFORM = f"{platform.platform()} | {platform.python_version()} | torch {torch.__version__}"

WATER = ""  # no Hebrew letters or marks: the baseline rate on every letter group

_model = None


def _tasting(job) -> Result:
    drives, seed, noise_hz, ms = job
    torch.set_num_threads(1)
    return _model.run(drives, ms, seed, noise_hz)


def _load() -> None:
    global _model
    _model = Model.from_connectome()


def workers(model: Model | None = None, method: str = "fork"):
    """Pool of the two tasting processes; use as a context manager. "fork" shares `model`;
    any other start method builds the whole-brain model in each worker."""
    global _model
    if method == "fork":
        _model = model
        return mp.get_context("fork").Pool(2)
    return mp.get_context(method).Pool(2, initializer=_load)


def taste_both(pool, drives_a, drives_b, seed: int, noise_hz: float,
               ms: float = TASTING_MS) -> tuple[Result, Result]:
    """Both tastings at once, same seed and noise."""
    jobs = [(drives_a, seed, noise_hz, ms), (drives_b, seed, noise_hz, ms)]
    return tuple(pool.map(_tasting, jobs, chunksize=1))


def brain(res_a: Result, res_b: Result, m: mood.Mood, seed: int) -> dict:
    """Stored "what happened in the brain?" summary: MN9 Hz per readout bin for each tasting;
    mood, seed, version, platform."""
    bin_s = OUTCOME["readout_bin_ms"] / 1000
    return {"bin_ms": OUTCOME["readout_bin_ms"],
            "mn9_hz": [(readout.mn9_bins(r) / bin_s).tolist() for r in (res_a, res_b)],
            "mood": {"hunger": m.hunger, "arousal": m.arousal}, "seed": seed,
            "sim_version": SIM_VERSION, "platform": PLATFORM}


def run(pool, text_a: str, text_b: str | None, seed: int, ms: float = TASTING_MS,
        wait_h: float | None = None) -> dict:
    """One hearing: mood, metrics + outcome, brain summary, wall-clock. `wait_h` is the real
    wait (2B); None draws it from the seed (2A). `text_b` None is plain water."""
    start = time.perf_counter()
    m = mood.product(seed) if wait_h is None else mood.from_case(seed, wait_h)
    b = WATER if text_b is None else text_b
    res = taste_both(pool, mood.tasting(text_a, m), mood.tasting(b, m), seed, m.noise_hz, ms)
    return {"seed": seed, "mood": {"hunger": m.hunger, "arousal": m.arousal},
            "metrics": readout.verdict(*res, m, ms / 1000), "brain": brain(*res, m, seed),
            "sim_version": SIM_VERSION, "platform": PLATFORM,
            "duration_ms": round((time.perf_counter() - start) * 1000)}

