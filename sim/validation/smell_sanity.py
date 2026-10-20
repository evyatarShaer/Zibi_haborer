"""P1-6 sanity check: three arguments → smell.drives → whole-brain model.

Run from sim/:  PYTHONPATH=src uv run python -m validation.smell_sanity
Reports ORN and downstream activity on one antenna, and wall-clock.
"""
import time

import numpy as np
import torch

from borer_sim import data, smell
from borer_sim.model import Model

ARGUMENTS = [
    "אתה תמיד שוכח לסגור את הדלת, וזה ממש מעצבן אותי",
    "הדבש שלי הכי טוב בעולם, תודה רבה!!!",
    "למה לא? מי אמר שפיצה עם אננס זה רע??",
]
SIDE, SEED, THREADS = "left", 783, 2


def main():
    torch.set_num_threads(THREADS)
    model = Model.from_connectome()
    classes = data.annotations()["super_class"].reindex(data.neuron_ids()).fillna("na").to_numpy()
    for text in ARGUMENTS:
        d = smell.drives(text, SIDE)
        driven = np.array(sorted(i for idx, _ in d for i in idx))
        mean_rate = sum(len(idx) * r for idx, r in d) / len(driven)
        for ms in (1000, 2000):
            t = time.perf_counter()
            r = model.run(d, ms, SEED)
            elapsed = time.perf_counter() - t
        rate = r.counts / 2.0  # last run is 2 s
        down = np.setdiff1d(r.active, driven)
        by_class = dict(zip(*np.unique(classes[down], return_counts=True)))
        pn = data.annotations()["cell_class"].reindex(data.neuron_ids()[down]).eq("ALPN").sum()
        print(f"\n{text}\n  driven ORNs {len(driven)} (mean {mean_rate:.1f} Hz), "
              f"spiking {np.count_nonzero(r.counts[driven])}, ORN rate {rate[driven].mean():.1f} Hz")
        print(f"  downstream active {len(down)} (ALPN {pn}), mean {rate[down].mean():.1f} Hz, "
              f"by class {by_class}")
        print(f"  wall-clock 2 s run: {elapsed:.2f} s")


if __name__ == "__main__":
    main()
