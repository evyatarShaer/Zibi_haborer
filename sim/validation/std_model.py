"""Prototype A: short-term depression on ORN -> PN synapses only (validation only).

Resource model (Tsodyks & Markram 1997 form): each ORN->ALPN synapse has
x in [0, 1], starting at 1. A spike arriving at step t delivers w * x
(so an isolated spike keeps the validated weight), then x <- x * (1 - U).
Between arrivals x recovers: x = 1 - (1 - x) * exp(-dt / tau_rec).
Constants U, tau_rec: Kazama & Wilson 2008 (see POC_REPORT). model.py is
not changed; this subclass re-implements Model._deliver with the extra
scaling (prototype duplication, to be folded into model.py if adopted).
"""
import torch

from borer_sim import data
from borer_sim.model import Model
from borer_sim.params import DT_MS


class STDModel(Model):
    def __init__(self, u: float, tau_rec_ms: float):
        super().__init__(*data.edges())
        cc = data.annotations()["cell_class"].reindex(data.neuron_ids()).fillna("na").to_numpy()
        pre_of_syn = torch.repeat_interleave(torch.arange(self.n), self.indptr[1:] - self.indptr[:-1])
        self.std = (torch.from_numpy(cc == "olfactory")[pre_of_syn]
                    & torch.from_numpy(cc == "ALPN")[self.post])
        self.u, self.steps_per_tau = u, tau_rec_ms / DT_MS

    def run(self, drives, duration_ms, seed):
        n_syn = len(self.w)
        self.x = torch.ones(n_syn)
        self.last = torch.zeros(n_syn)
        self.t = -1
        return super().run(drives, duration_ms, seed)

    def _deliver(self, g, pre):
        self.t += 1  # Model.run calls _deliver exactly once per step
        start, lens = self.indptr[pre], self.indptr[pre + 1] - self.indptr[pre]
        total = int(lens.sum())
        if total == 0:
            return
        offset = torch.arange(total) - torch.repeat_interleave(lens.cumsum(0) - lens, lens)
        syn = torch.repeat_interleave(start, lens) + offset
        w = self.w[syn].clone()
        mask = self.std[syn]
        if mask.any():
            s = syn[mask]
            x = 1 - (1 - self.x[s]) * torch.exp(-(self.t - self.last[s]) / self.steps_per_tau)
            w[mask] *= x
            self.x[s] = x * (1 - self.u)
            self.last[s] = float(self.t)
        g.index_add_(0, self.post[syn], w)
