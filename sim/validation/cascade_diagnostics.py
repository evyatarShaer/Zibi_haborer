"""Where does the olfactory cascade live? (diagnostics, 2026-10-20)

Run from sim/:  PYTHONPATH=src uv run python -m validation.cascade_diagnostics
Rebuilds the model with edge subsets (validation only; model.py unchanged):
- "no input to ORNs": drop every synapse onto an ORN (axo-axonal input
  can't make a real ORN fire — its spikes start in the antenna);
- "no KC->KC": drop Kenyon-cell -> Kenyon-cell synapses.
Also counts edges strong enough for 1-3 coincident spikes to fire the target.
"""
import numpy as np
import torch

from borer_sim import data
from borer_sim.model import Model
from borer_sim.params import LIF
from validation.steering import metrics
from validation.steering_probe import X_TEXTS, Y_TEXTS, balanced, hearing
from validation.sugar_mn9 import MN9, conditions

SEEDS = (783, 784)


def spikes_needed() -> float:
    """Synapse count at which one presynaptic spike alone fires the target."""
    tm, tau = LIF["t_mbr"], LIF["tau"]
    t_peak = np.log(tm / tau) * tau * tm / (tm - tau)
    peak = tau / (tm - tau) * (np.exp(-t_peak / tm) - np.exp(-t_peak / tau))
    return (LIF["v_th"] - LIF["v_0"]) / (peak * LIF["w_syn"])


def main():
    torch.set_num_threads(4)
    n, pre, post, w = data.edges()
    cc = data.annotations()["cell_class"].reindex(data.neuron_ids()).fillna("na").to_numpy()
    need = spikes_needed()
    for k in (1, 2, 3):
        print(f"edges firing the target with {k} coincident spike(s) (>= {need / k:.0f} syn): "
              f"{(w >= need / k).sum():,}")
    orn, kc = cc == "olfactory", cc == "Kenyon_Cell"
    variants = {"full": np.ones(len(pre), bool),
                "no input to ORNs": ~orn[post],
                "no KC->KC": ~(kc[pre] & kc[post])}
    drives = {"hearing x_nat|y_nat": hearing(X_TEXTS["x_nat"], Y_TEXTS["y_nat"]),
              "DL2d left 20 Hz": balanced("DL2d", "left", 20.0),
              "DM1 left 60 Hz": balanced("DM1", "left", 60.0),
              "DM1 right 60 Hz": balanced("DM1", "right", 60.0)}
    mn9 = data.to_index(list(MN9.values()))
    for vname, keep in variants.items():
        model = Model(n, pre[keep], post[keep], w[keep])
        print(f"\n{vname}: {(~keep).sum():,} edge rows removed")
        for dname, d in drives.items():
            for seed in SEEDS:
                r = model.run(d, 1000, seed)
                m = metrics(r.counts)
                print(f"  {dname:20s} seed {seed}: active {m['active']:5d} "
                      f"(KC {int((r.counts[kc] > 0).sum()):4d})  DNa02 L/R "
                      f"{m['DNa02'][0]:.0f}/{m['DNa02'][1]:.0f}")
        r = model.run(conditions()["sugar200"], 1000, SEEDS[0])
        print(f"  sugar200 MN9 Hz: {r.counts[mn9].tolist()}  (P1-5 ref 88.9 / 62.4)")


if __name__ == "__main__":
    main()
