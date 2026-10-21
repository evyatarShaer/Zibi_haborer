"""Whole-brain LIF model in PyTorch (CPU) — Shiu et al. 2024 dynamics.

Matches sim/validation/shiu_brian2.py step for step. Each DT_MS step:
1. exact (linear) integration of  dv/dt = (v_0 - v + g) / t_mbr,
   dg/dt = -g / tau;
2. threshold v > v_th;
3. delivery of spikes emitted t_dly ago (g += w) and Poisson input
   (v += f_poi * w_syn);
4. reset v = v_rst, g = 0 for neurons that spiked.
Refractory neurons keep v and g unchanged through steps 1–3: Brian2's
"(unless refractory)" is a conditional write, so synaptic input that
arrives during refractoriness is discarded, not deferred.
State is kept as u = v - v_0. One seed drives every random draw.
"""
import math
from collections import deque
from dataclasses import dataclass

import numpy as np
import torch

from borer_sim import data
from borer_sim.params import BIN_MS, DT_MS, LIF


@dataclass(frozen=True)
class Result:
    counts: np.ndarray  # (n_neurons,) int32 spikes per neuron
    active: np.ndarray  # (n_active,) sorted model indices with >= 1 spike
    binned: np.ndarray  # (n_bins, n_active) int32 spikes per BIN_MS bin


class Model:
    """Connectome weights as CSR rows by presynaptic neuron."""

    def __init__(self, n: int, pre: np.ndarray, post: np.ndarray, signed_count: np.ndarray):
        self.n = n
        self.keep = None  # full-brain indices of a subcircuit's neurons (None = whole brain)
        self.full_n = n  # size of results: run() returns full-brain arrays
        order = np.argsort(pre, kind="stable")
        indptr = np.concatenate([[0], np.cumsum(np.bincount(pre, minlength=n))])
        self.indptr = torch.from_numpy(indptr)
        self.post = torch.from_numpy(np.asarray(post, dtype=np.int64)[order])
        w = np.asarray(signed_count)[order] * LIF["w_syn"]
        self.w = torch.from_numpy(w.astype(np.float32))

    @classmethod
    def from_connectome(cls) -> "Model":
        """The whole-brain FlyWire v783 model."""
        return cls(*data.edges())

    @classmethod
    def subcircuit(cls, keep) -> "Model":
        """Model of the neurons `keep` (sorted full-brain indices), edges among them only.

        run() takes and returns full-brain indices, so readouts are unchanged."""
        n, pre, post, w = data.edges()
        keep = np.asarray(keep, dtype=np.int64)
        local = np.full(n, -1, dtype=np.int64)
        local[keep] = np.arange(len(keep))
        m = (local[pre] >= 0) & (local[post] >= 0)
        model = cls(len(keep), local[pre[m]], local[post[m]], w[m])
        model.keep, model._local, model.full_n = keep, local, n
        return model

    def _deliver(self, g: torch.Tensor, pre: torch.Tensor) -> None:
        """g[post] += w for every synapse of the presynaptic neurons `pre`."""
        start, lens = self.indptr[pre], self.indptr[pre + 1] - self.indptr[pre]
        total = int(lens.sum())
        if total == 0:
            return
        offset = torch.arange(total) - torch.repeat_interleave(lens.cumsum(0) - lens, lens)
        syn = torch.repeat_interleave(start, lens) + offset
        g.index_add_(0, self.post[syn], self.w[syn])

    def run(self, drives: list[tuple[list[int], float]], duration_ms: float,
            seed: int) -> Result:
        """Simulate `duration_ms` with Poisson drive [(model indices, rate Hz)]."""
        if self.keep is not None:
            drives = [(self._local[np.asarray(idx, dtype=np.int64)], r) for idx, r in drives]
            if any((idx < 0).any() for idx, _ in drives):
                raise ValueError("drive targets a neuron outside the subcircuit")
            return self._expand(self._simulate(drives, duration_ms, seed))
        return self._simulate(drives, duration_ms, seed)

    def _expand(self, r: Result) -> Result:
        counts = np.zeros(self.full_n, dtype=np.int32)
        counts[self.keep] = r.counts
        return Result(counts, self.keep[r.active], r.binned)

    def _simulate(self, drives, duration_ms: float, seed: int) -> Result:
        p = LIF
        steps = round(duration_ms / DT_MS)
        ev, eg = math.exp(-DT_MS / p["t_mbr"]), math.exp(-DT_MS / p["tau"])
        c = p["tau"] / (p["tau"] - p["t_mbr"]) * (eg - ev)
        th, u_rst = p["v_th"] - p["v_0"], p["v_rst"] - p["v_0"]
        w_poi = p["f_poi"] * p["w_syn"]

        targets = torch.tensor([int(i) for idx, _ in drives for i in idx], dtype=torch.long)
        prob = torch.tensor([r * DT_MS / 1000 for idx, r in drives for _ in idx])
        gen = torch.Generator().manual_seed(seed)
        hits = torch.rand((steps, len(targets)), generator=gen) < prob

        has_rfc = torch.ones(self.n, dtype=torch.bool)
        has_rfc[targets] = False  # Shiu: no refractory period for driven neurons
        u = torch.zeros(self.n)
        g = torch.zeros(self.n)
        delayed = deque([torch.empty(0, dtype=torch.long)] * round(p["t_dly"] / DT_MS))
        refractory = deque([torch.empty(0, dtype=torch.long)] * (round(p["t_rfc"] / DT_MS) - 1))
        spikes = []

        for t in range(steps):
            frozen = torch.cat(tuple(refractory))
            u_old, g_old = u[frozen], g[frozen]
            u.mul_(ev).add_(g, alpha=c)
            g.mul_(eg)

            spk = torch.nonzero(u > th).squeeze(1)  # frozen u stays at u_rst < th
            self._deliver(g, delayed.popleft())
            delayed.append(spk)
            if len(targets):
                u.index_add_(0, targets[hits[t]], torch.full((int(hits[t].sum()),), w_poi))
            u[frozen], g[frozen] = u_old, g_old  # discard this step's writes
            u[spk], g[spk] = u_rst, 0.0

            refractory.popleft()
            refractory.append(spk[has_rfc[spk]])
            spikes.append(spk)
        return _result(spikes, self.n, steps)


def _result(spikes: list[torch.Tensor], n: int, steps: int) -> Result:
    idx = torch.cat(spikes).numpy()
    step = np.repeat(np.arange(steps), [len(s) for s in spikes])
    counts = np.bincount(idx, minlength=n).astype(np.int32)
    active = np.flatnonzero(counts)
    per_bin = round(BIN_MS / DT_MS)
    n_bins = math.ceil(steps / per_bin)
    binned = np.zeros((n_bins, len(active)), dtype=np.int32)
    np.add.at(binned, (step // per_bin, np.searchsorted(active, idx)), 1)
    return Result(counts, active, binned)
