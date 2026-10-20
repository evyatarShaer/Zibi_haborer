"""Brian2 port of Shiu et al. 2024's whole-brain LIF model — validation only.

Mirrors model.py from philshiu/Drosophila_brain_model (MIT, (c) 2023
Philip Shiu and Nico Spiller): same equations, parameters and Poisson
drive. Differences are mechanical only: the network is built once per
condition and reused across trials via store/restore, and every trial is
seeded. Brian2 must stay out of borer_sim/ (see pyproject.toml).
"""
from textwrap import dedent

import numpy as np
from brian2 import (Hz, Network, NeuronGroup, PoissonInput, SpikeMonitor,
                    Synapses, mV, ms, prefs, seed)

from borer_sim import data
from borer_sim.params import LIF

prefs.codegen.target = "cython"

UNITS = {"v_0": mV, "v_rst": mV, "v_th": mV, "t_mbr": ms, "tau": ms,
         "t_rfc": ms, "t_dly": ms, "w_syn": mV, "f_poi": 1}
PARAMS = {k: v * UNITS[k] for k, v in LIF.items()} | {"t_run": 1000 * ms}

EQS = dedent("""
    dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
    dg/dt = -g / tau               : volt (unless refractory)
    rfc                            : second
""")


def build(drives: list[tuple[list[int], float]], edges=None) -> tuple[Network, SpikeMonitor]:
    """Network with Poisson drive; whole brain unless `edges` is given.

    drives: (model indices, rate in Hz) pairs — Shiu's `exc` / `exc2`.
    edges: (n, pre, post, signed_count) as returned by data.edges().
    """
    p = PARAMS
    n, pre, post, signed_count = edges if edges is not None else data.edges()
    neu = NeuronGroup(n, EQS, method="linear",
                      threshold="v > v_th", reset="v = v_rst; g = 0 * mV",
                      refractory="rfc", namespace=p, name="neurons")
    neu.v = p["v_0"]
    neu.g = 0 * mV
    neu.rfc = p["t_rfc"]

    syn = Synapses(neu, neu, "w : volt", on_pre="g += w", delay=p["t_dly"])
    syn.connect(i=pre, j=post)
    syn.w = signed_count * p["w_syn"]

    pois = []
    for idx, rate in drives:
        for i in idx:
            pois.append(PoissonInput(neu[i:i + 1], "v", N=1, rate=rate * Hz,
                                     weight=p["w_syn"] * p["f_poi"]))
            neu.rfc[i] = 0 * ms  # Shiu: no refractory period for driven neurons
    mon = SpikeMonitor(neu, record=edges is not None)  # small nets: keep spike times
    return Network(neu, syn, mon, *pois), mon


def run_trials(drives, n_trials: int, base_seed: int) -> np.ndarray:
    """Spike counts, shape (n_trials, n_neurons). Trial k uses seed base_seed + k."""
    net, mon = build(drives)
    net.store()
    counts = []
    for k in range(n_trials):
        net.restore()
        seed(base_seed + k)
        net.run(PARAMS["t_run"])
        counts.append(np.asarray(mon.count[:], dtype=np.int32))
    return np.stack(counts)
