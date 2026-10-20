"""Prototypes A (ORN->PN short-term depression) and B (taste of words).

Run from sim/:
    PYTHONPATH=src uv run python -m validation.proto_probe <tag> <U> <tau_rec_ms>
      a1: U=0.22, tau_rec=893 ms — Nagel, Hong & Wilson 2015 fit (f=0.78, tau=893 ms)
      a2: U=0.79, tau_rec=893 ms — Kazama & Wilson 2008 release probability as depletion
    PYTHONPATH=src uv run python -m validation.proto_probe b
Keys: side runs "lvl|text|side|seed", swap runs "x|y|XY/YX|seed".
"""
import sys

from borer_sim import anatomy, smell
from validation import steering, taste
from validation.readout_probe import pop_metrics
from validation.std_model import STDModel
from validation.steering_probe import THREADS, WORKERS, X_TEXTS, Y_TEXTS
from validation.sugar_mn9 import OUT

MATCHED = list(zip(X_TEXTS, Y_TEXTS))
CROSS = [("x_att", "y_ave"), ("x_ave", "y_att"), ("x_neu", "y_att"),
         ("x_nat", "y_ave"), ("x_q", "y_att")]
SEEDS = tuple(range(783, 793))


def side_jobs(drive_fn, texts, levels, seeds):
    return {f"{lvl}|{t}|{side}|{seed}": (drive_fn(X_TEXTS[t], side, lvl), seed)
            for lvl in levels for t in texts for side in anatomy.SIDES for seed in seeds}


def swap_jobs(drive_fn, pairs, seeds):
    jobs = {}
    for x, y in pairs:
        for seed in seeds:
            for order, (lt, rt) in (("XY", (X_TEXTS[x], Y_TEXTS[y])), ("YX", (Y_TEXTS[y], X_TEXTS[x]))):
                jobs[f"{x}|{y}|{order}|{seed}"] = (drive_fn(lt, "left") + drive_fn(rt, "right"), seed)
    return jobs


def smell_drive(text, side, scale=1.0):
    return [(idx, r * scale) for idx, r in smell.drives(text, side)]


def run(name, jobs, model=None):
    print(f"{name}: {len(jobs)} jobs", flush=True)
    steering.run_jobs(jobs, OUT / name, WORKERS, THREADS, metric=pop_metrics, model=model)


def prototype_a(tag, u, tau_rec_ms):
    model = STDModel(u, tau_rec_ms)
    print(f"STD on {model.n_std:,} ORN->PN synapse rows, U={u}, tau_rec={tau_rec_ms} ms")
    run(f"proto_{tag}_side.jsonl", side_jobs(smell_drive, ["x_nat"], (0.1, 0.3, 1.0), SEEDS[:2]), model)
    run(f"proto_{tag}_swap.jsonl", swap_jobs(smell_drive, MATCHED, SEEDS[:5]), model)


def prototype_b():
    print(taste.inventory().to_string())
    for key, (name, ids) in taste.mapping().items():
        print(f"  {key} -> {name} ({len(ids)} GRNs)")
    run("proto_b_side.jsonl", side_jobs(taste.drives, ["x_att", "x_ave", "x_nat"],
                                        (0.25, 0.5, 1.0), SEEDS[:5]))
    run("proto_b_swap.jsonl", swap_jobs(taste.drives, MATCHED + CROSS, SEEDS))


if __name__ == "__main__":
    if sys.argv[1] == "b":
        prototype_b()
    else:
        prototype_a(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
