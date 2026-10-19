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

prefs.codegen.target = "cython"

PARAMS = {
    "t_run": 1000 * ms,
    "v_0": -52 * mV,
    "v_rst": -52 * mV,
    "v_th": -45 * mV,
    "t_mbr": 20 * ms,
    "tau": 5 * ms,
    "t_rfc": 2.2 * ms,
    "t_dly": 1.8 * ms,
    "w_syn": 0.275 * mV,
    "f_poi": 250,
}

EQS = dedent("""
    dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
    dg/dt = -g / tau               : volt (unless refractory)
    rfc                            : second
""")


def build(drives: list[tuple[list[int], float]]) -> tuple[Network, SpikeMonitor]:
    """Whole-brain network with Poisson drive.

    drives: (model indices, rate in Hz) pairs — Shiu's `exc` / `exc2`.
    """
    p = PARAMS
    con = data.connectivity()
    neu = NeuronGroup(len(data.neuron_ids()), EQS, method="linear",
                      threshold="v > v_th", reset="v = v_rst; g = 0 * mV",
                      refractory="rfc", namespace=p, name="neurons")
    neu.v = p["v_0"]
    neu.g = 0 * mV
    neu.rfc = p["t_rfc"]

    syn = Synapses(neu, neu, "w : volt", on_pre="g += w", delay=p["t_dly"])
    syn.connect(i=con["Presynaptic_Index"].to_numpy(),
                j=con["Postsynaptic_Index"].to_numpy())
    syn.w = con["Excitatory x Connectivity"].to_numpy() * p["w_syn"]

    pois = []
    for idx, rate in drives:
        for i in idx:
            pois.append(PoissonInput(neu[i:i + 1], "v", N=1, rate=rate * Hz,
                                     weight=p["w_syn"] * p["f_poi"]))
            neu.rfc[i] = 0 * ms  # Shiu: no refractory period for driven neurons
    mon = SpikeMonitor(neu, record=False)
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
